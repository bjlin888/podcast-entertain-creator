from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_user_id
from app.db import (
    create_project,
    delete_project_cascade,
    get_db,
    get_project,
    get_projects_by_user,
    get_titles_by_project,
    get_current_script,
    get_segments_by_script,
    update_project,
)
from app.models import CreateProjectRequest, UpdateProjectRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["projects"])


@router.get("/projects")
async def list_projects(user_id: str = Depends(get_user_id)):
    """List all projects for the authenticated user."""
    async with get_db() as db:
        projects = await get_projects_by_user(db, user_id)
    return {"projects": projects}


@router.post("/projects", status_code=201)
async def create_project_endpoint(
    body: CreateProjectRequest,
    user_id: str = Depends(get_user_id),
):
    """Create a new project."""
    async with get_db() as db:
        project_id = await create_project(
            db,
            user_id=user_id,
            topic=body.topic,
            audience=body.audience,
            duration_min=body.duration_min,
            style=body.style,
            host_count=body.host_count,
            llm_provider=body.llm_provider,
            cover_index=body.cover_index,
        )
        project = await get_project(db, project_id)
    return {"project": project}


@router.get("/projects/{project_id}")
async def get_project_detail(
    project_id: str,
    user_id: str = Depends(get_user_id),
):
    """Get project detail including titles and current script segments."""
    async with get_db() as db:
        project = await get_project(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        titles = await get_titles_by_project(db, project_id)

        script = await get_current_script(db, project_id)
        segments = []
        if script:
            segments = await get_segments_by_script(db, script["script_id"])

    return {
        "project": project,
        "titles": titles,
        "script": script,
        "segments": segments,
    }


@router.patch("/projects/{project_id}")
async def update_project_endpoint(
    project_id: str,
    body: UpdateProjectRequest,
    user_id: str = Depends(get_user_id),
):
    """Partial update of project fields."""
    async with get_db() as db:
        project = await get_project(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        fields = body.model_dump(exclude_none=True)
        if fields:
            await update_project(db, project_id, **fields)
        updated = await get_project(db, project_id)
    return {"project": updated}


@router.delete("/projects/{project_id}", status_code=204)
async def delete_project_endpoint(
    project_id: str,
    user_id: str = Depends(get_user_id),
):
    """Delete a project and all related data."""
    async with get_db() as db:
        project = await get_project(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
        await delete_project_cascade(db, project_id)
    return None
