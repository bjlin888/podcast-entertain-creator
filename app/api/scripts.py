from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_user_id
from app.api.rate_limit import _limiter
from app.db import (
    create_script,
    create_segments,
    get_current_script,
    get_db,
    get_project,
    get_segment,
    get_segments_by_script,
    get_titles_by_project,
    update_segment,
)
from app.llm.factory import get_provider_for_user
from app.llm.prompt_builder import load_prompt
from app.models import SegmentEditRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["scripts"])

# Map project style to 三層十段 structure variant
STYLE_TO_VARIANT = {
    "訪談對話": "訪談型",
    "知識分享": "獨白型",
    "深度分析": "獨白型",
    "幽默搞笑": "獨白型",
    "輕鬆聊天": "獨白型",
    "新聞評論": "獨白型",
}


@router.post("/projects/{project_id}/scripts/generate")
async def generate_script(
    project_id: str,
    user_id: str = Depends(get_user_id),
):
    """Generate a script via LLM, save script + segments, return them."""
    _limiter.check(f"{user_id}:scripts", max_calls=5, window_seconds=60)

    async with get_db() as db:
        project = await get_project(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        llm_provider = project.get("llm_provider") or "gemini"

        # Find selected title
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
            logger.exception("Script generation failed: project=%s user=%s", project_id, user_id)
            raise HTTPException(status_code=502, detail="Script generation failed")

        # Determine version
        current = await get_current_script(db, project_id)
        version = (current["version"] + 1) if current else 1

        script_id = await create_script(db, project_id, version=version)
        await create_segments(db, script_id, segments_data)
        db_segments = await get_segments_by_script(db, script_id)

        script = await get_current_script(db, project_id)

    return {
        "script": script,
        "segments": db_segments,
    }


@router.get("/projects/{project_id}/scripts/current")
async def get_current_script_endpoint(
    project_id: str,
    user_id: str = Depends(get_user_id),
):
    """Get the current script and its segments."""
    async with get_db() as db:
        project = await get_project(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        script = await get_current_script(db, project_id)
        if not script:
            raise HTTPException(status_code=404, detail="No script found")

        segments = await get_segments_by_script(db, script["script_id"])

    return {
        "script": script,
        "segments": segments,
    }


@router.patch("/scripts/segments/{segment_id}")
async def edit_segment(
    segment_id: str,
    body: SegmentEditRequest,
    user_id: str = Depends(get_user_id),
):
    """Directly edit a segment's content."""
    async with get_db() as db:
        segment = await get_segment(db, segment_id)
        if not segment:
            raise HTTPException(status_code=404, detail="Segment not found")

        # Verify ownership through script -> project -> user chain
        cursor = await db.execute(
            """SELECT p.user_id FROM projects p
               JOIN scripts s ON p.project_id = s.project_id
               WHERE s.script_id = ?""",
            (segment["script_id"],),
        )
        row = await cursor.fetchone()
        if not row or row[0] != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        await update_segment(db, segment_id, body.content)
        updated = await get_segment(db, segment_id)

    return {"segment": updated}


@router.post("/scripts/segments/{segment_id}/refine")
async def refine_segment(
    segment_id: str,
    body: SegmentEditRequest,
    user_id: str = Depends(get_user_id),
):
    """LLM-powered refinement of a segment based on feedback text."""
    _limiter.check(f"{user_id}:refine", max_calls=10, window_seconds=60)

    async with get_db() as db:
        segment = await get_segment(db, segment_id)
        if not segment:
            raise HTTPException(status_code=404, detail="Segment not found")

        # Verify ownership
        cursor = await db.execute(
            """SELECT p.user_id, p.llm_provider FROM projects p
               JOIN scripts s ON p.project_id = s.project_id
               WHERE s.script_id = ?""",
            (segment["script_id"],),
        )
        row = await cursor.fetchone()
        if not row or row[0] != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        llm_provider = row[1] or "gemini"

        try:
            provider = await get_provider_for_user(user_id, llm_provider)
            system = load_prompt("system")
            user_msg = load_prompt(
                "script_refinement",
                original_content=segment["content"],
                feedback=body.content,
                scores="N/A",
                segment_type=segment.get("segment_type") or "main",
                label=segment.get("label") or "",
            )
            result = await provider.complete(system, user_msg, task="script_refinement")
            new_content = result.get("content", segment["content"])
        except Exception:
            logger.exception("Segment refinement failed: segment=%s user=%s", segment_id, user_id)
            raise HTTPException(status_code=502, detail="Segment refinement failed")

        await update_segment(db, segment_id, new_content)
        updated = await get_segment(db, segment_id)

    return {"segment": updated}
