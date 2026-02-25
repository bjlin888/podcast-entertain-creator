from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_user_id
from app.api.rate_limit import _limiter
from app.db import (
    create_feedback,
    create_script,
    create_segments,
    get_current_script,
    get_db,
    get_project,
    get_segments_by_script,
    get_titles_by_project,
)
from app.api.scripts import STYLE_TO_VARIANT
from app.llm.factory import get_provider_for_user
from app.llm.prompt_builder import load_prompt
from app.models import FeedbackRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["feedback"])


@router.post("/projects/{project_id}/feedback")
async def submit_feedback(
    project_id: str,
    body: FeedbackRequest,
    user_id: str = Depends(get_user_id),
):
    """Submit feedback scores + text, optionally trigger script regeneration.

    If text_feedback is provided and the average score is below 4,
    a new script version is automatically generated.
    """
    _limiter.check(f"{user_id}:feedback", max_calls=5, window_seconds=60)

    async with get_db() as db:
        project = await get_project(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        script = await get_current_script(db, project_id)
        if not script:
            raise HTTPException(status_code=404, detail="No script found for this project")

        # Save feedback record
        feedback_id = await create_feedback(
            db,
            script_id=script["script_id"],
            score_content=body.score_content,
            score_engagement=body.score_engagement,
            score_structure=body.score_structure,
            text_feedback=body.text_feedback,
        )

        # Determine if we should regenerate the script
        regenerated = False
        new_script = None
        new_segments = None

        scores = [s for s in [body.score_content, body.score_engagement, body.score_structure] if s is not None]
        avg_score = sum(scores) / len(scores) if scores else 5.0

        if body.text_feedback and avg_score < 4:
            # Trigger script regeneration
            llm_provider = project.get("llm_provider") or "gemini"

            titles = await get_titles_by_project(db, project_id)
            selected = next((t for t in titles if t["is_selected"]), None)
            selected_title = selected["title_zh"] if selected else project["topic"]

            try:
                provider = await get_provider_for_user(user_id, llm_provider)
                style_value = project["style"] or "輕鬆閒聊"
                structure_variant = STYLE_TO_VARIANT.get(style_value, "獨白型")
                system = load_prompt("system")
                user_msg = load_prompt(
                    "script_generation",
                    selected_title=selected_title,
                    topic=project["topic"],
                    audience=project["audience"],
                    style=style_value,
                    duration_min=str(project["duration_min"] or 30),
                    host_count=str(project["host_count"] or 1),
                    structure_variant=structure_variant,
                )
                result = await provider.complete(system, user_msg, task="script_generation")
                segments_data = result.get("segments", [])
            except Exception:
                logger.exception(
                    "Script regeneration from feedback failed: project=%s user=%s",
                    project_id,
                    user_id,
                )
                raise HTTPException(status_code=502, detail="Script regeneration failed")

            version = script["version"] + 1
            new_script_id = await create_script(db, project_id, version=version)
            await create_segments(db, new_script_id, segments_data)

            new_script = await get_current_script(db, project_id)
            new_segments = await get_segments_by_script(db, new_script_id)
            regenerated = True

    response = {
        "feedback_id": feedback_id,
        "regenerated": regenerated,
    }
    if regenerated:
        response["script"] = new_script
        response["segments"] = new_segments

    return response
