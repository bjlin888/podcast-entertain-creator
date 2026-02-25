from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_user_id
from app.api.rate_limit import _limiter
from app.db import (
    create_titles,
    delete_titles_by_project,
    get_db,
    get_project,
    get_title,
    get_titles_by_project,
    select_title,
)
from app.llm.factory import get_provider
from app.llm.prompt_builder import load_prompt

logger = logging.getLogger(__name__)

router = APIRouter(tags=["titles"])


@router.post("/projects/{project_id}/titles/generate")
async def generate_titles(
    project_id: str,
    user_id: str = Depends(get_user_id),
):
    """Generate 5 candidate titles via LLM, save to DB, and return them."""
    _limiter.check(f"{user_id}:titles", max_calls=10, window_seconds=60)

    async with get_db() as db:
        project = await get_project(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        llm_provider = project.get("llm_provider") or "gemini"

        try:
            provider = get_provider(llm_provider)
            system = load_prompt("system")
            user_msg = load_prompt(
                "title_generation",
                topic=project["topic"],
                audience=project["audience"],
                style=project["style"] or "輕鬆閒聊",
            )
            result = await provider.complete(system, user_msg, task="title_generation")
            titles_data = result.get("titles", [])[:5]
        except Exception:
            logger.exception("Title generation failed: project=%s user=%s", project_id, user_id)
            raise HTTPException(status_code=502, detail="Title generation failed")

        # Delete old titles and insert new ones
        await delete_titles_by_project(db, project_id)
        await create_titles(db, project_id, titles_data)
        db_titles = await get_titles_by_project(db, project_id)

    return {"titles": db_titles}


@router.get("/projects/{project_id}/titles")
async def list_titles(
    project_id: str,
    user_id: str = Depends(get_user_id),
):
    """List all titles for a project."""
    async with get_db() as db:
        project = await get_project(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        titles = await get_titles_by_project(db, project_id)

    return {"titles": titles}


@router.post("/projects/{project_id}/titles/{title_id}/select")
async def select_title_endpoint(
    project_id: str,
    title_id: str,
    user_id: str = Depends(get_user_id),
):
    """Mark a title as selected."""
    async with get_db() as db:
        project = await get_project(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        title = await get_title(db, title_id)
        if not title:
            raise HTTPException(status_code=404, detail="Title not found")
        if title["project_id"] != project_id:
            raise HTTPException(status_code=400, detail="Title does not belong to this project")

        await select_title(db, title_id)
        updated_title = await get_title(db, title_id)

    return {"title": updated_title}
