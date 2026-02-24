from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
)
from linebot.v3.webhook import WebhookParser

from app.config import settings
from app.db import get_db, init_db, upsert_user, get_or_create_session, update_session
from app.state_machine import process_event

import app.handlers  # noqa: F401 — trigger handler registration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

parser = WebhookParser(channel_secret=settings.line_channel_secret)
configuration = Configuration(access_token=settings.line_channel_access_token)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db(settings.database_url)
    from app.tts.audio_storage import init_audio_dir

    init_audio_dir()
    logger.info("App started, DB initialized, audio dir ready")
    yield


app = FastAPI(lifespan=lifespan)

# Serve TTS audio files
_audio_dir = Path("data/audio")
_audio_dir.mkdir(parents=True, exist_ok=True)
app.mount("/audio", StaticFiles(directory=str(_audio_dir)), name="audio")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature", "")
    body = (await request.body()).decode("utf-8")
    logger.info("Webhook received, body length=%d", len(body))
    logger.debug("Webhook body: %s", body[:500])

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        logger.warning("Invalid signature: %s", signature)
        raise HTTPException(status_code=400, detail="Invalid signature")

    logger.info("Parsed %d event(s)", len(events))

    for event in events:
        event_type = type(event).__name__
        user_id = getattr(event.source, "user_id", None)
        logger.info("Event: type=%s, user_id=%s", event_type, user_id)
        try:
            await _handle_event(event)
        except Exception:
            logger.exception("Error handling event: %s", event_type)

    return "OK"


async def _handle_event(event) -> None:
    user_id = getattr(event.source, "user_id", None)
    if not user_id:
        logger.warning("Event has no user_id, skipping: %s", type(event).__name__)
        return

    async with get_db() as db:
        await upsert_user(db, user_id, display_name="User")
        session = await get_or_create_session(db, user_id)
        logger.info(
            "Session: state=%s, project_id=%s",
            session["state"],
            session.get("project_id"),
        )

        async with AsyncApiClient(configuration) as api_client:
            api = AsyncMessagingApi(api_client)
            next_state = await process_event(event, session, db, api)
            logger.info("State transition: %s → %s", session["state"], next_state.value)
            await update_session(db, session["session_id"], state=next_state.value)


