from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db(settings.database_url)
    from app.tts.audio_storage import init_audio_dir

    init_audio_dir()
    logger.info("App started, DB initialized, audio dir ready")
    yield


app = FastAPI(title="Podcast 創作助手 API", lifespan=lifespan)

# CORS from environment variable
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-User-Id"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    user_id = request.headers.get("X-User-Id", "-")
    response = await call_next(request)
    ms = (time.time() - start) * 1000
    logger.info(
        "%s %s user=%s status=%d %.0fms",
        request.method,
        request.url.path,
        user_id[:8],
        response.status_code,
        ms,
    )
    return response


# Mount API routers
from app.api.projects import router as projects_router
from app.api.titles import router as titles_router
from app.api.scripts import router as scripts_router
from app.api.tts import router as tts_router
from app.api.feedback import router as feedback_router
from app.api.export import router as export_router

@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(projects_router, prefix="/api/v1")
app.include_router(titles_router, prefix="/api/v1")
app.include_router(scripts_router, prefix="/api/v1")
app.include_router(tts_router, prefix="/api/v1")
app.include_router(feedback_router, prefix="/api/v1")
app.include_router(export_router, prefix="/api/v1")

# Serve TTS audio files
_audio_dir = Path("data/audio")
_audio_dir.mkdir(parents=True, exist_ok=True)
app.mount("/audio", StaticFiles(directory=str(_audio_dir)), name="audio")

# Serve frontend in production (must be last — catch-all)
_frontend_dist = Path("frontend/dist")
if _frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
