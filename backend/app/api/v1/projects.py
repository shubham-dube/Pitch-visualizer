"""
Projects API — v1.

POST   /projects                  Create + trigger generation
GET    /projects                  List all projects
GET    /projects/{id}             Full project detail
DELETE /projects/{id}             Delete project
GET    /projects/{id}/status      Lightweight polling
POST   /projects/{id}/regenerate  Regenerate entire storyboard
"""
from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.config import Settings, get_settings
from app.dependencies import get_pipeline, get_store
from app.models.api_schemas import (
    CreateProjectRequest,
    CreateProjectResponse,
    PanelDetailResponse,
    PanelSummaryResponse,
    ProjectDetailResponse,
    ProjectSummaryResponse,
    ProgressResponse,
    RegenerateProjectRequest,
    StatusResponse,
    StoryboardResponse,
)
from app.models.enums import PanelStatus, ProjectStatus
from app.models.project import GenerationConfig, PanelModel, ProjectModel
from app.store.base import BaseStore
from app.utils.errors import ProjectNotFoundError

router = APIRouter(prefix="/projects", tags=["Projects"])


# ── Helpers ───────────────────────────────────────────────────────

def _progress_to_response(p) -> ProgressResponse:
    return ProgressResponse(
        percent=p.percent,
        current_stage=p.current_stage,
        completed_panels=p.completed_panels,
        total_panels=p.total_panels,
        elapsed_seconds=p.elapsed_seconds,
        estimated_remaining_seconds=p.estimated_remaining_seconds,
    )


def _panel_to_detail(p: PanelModel) -> PanelDetailResponse:
    return PanelDetailResponse(
        panel_index=p.panel_index,
        scene_title=p.scene_title,
        original_text=p.original_text,
        engineered_prompt=p.engineered_prompt,
        visual_prompt=p.visual_prompt,
        image_url=p.image_url,
        mood=p.mood,
        panel_role=p.panel_role,
        dominant_emotion=p.dominant_emotion,
        intensity=p.intensity,
        color_palette=p.color_palette,
        key_elements=p.key_elements,
        dalle_revised_prompt=p.generation_meta.dalle_revised_prompt,
        generation_time_ms=p.generation_meta.generation_time_ms,
        estimated_cost_usd=p.generation_meta.estimated_cost_usd,
        model_used=p.generation_meta.model_used,
        retry_count=p.generation_meta.retry_count,
        status=p.status,
        error=p.error,
    )


def _panel_to_summary(p: PanelModel) -> PanelSummaryResponse:
    return PanelSummaryResponse(
        panel_index=p.panel_index,
        scene_title=p.scene_title,
        image_url=p.image_url,
        mood=p.mood,
        panel_role=p.panel_role,
        dominant_emotion=p.dominant_emotion,
        intensity=p.intensity,
        color_palette=p.color_palette,
        status=p.status,
        error=p.error,
    )


def _project_to_detail(proj: ProjectModel) -> ProjectDetailResponse:
    storyboard = None
    if proj.storyboard:
        storyboard = StoryboardResponse(
            overall_arc=proj.storyboard.overall_arc,
            panels=[_panel_to_detail(p) for p in proj.storyboard.panels],
            assembled_at=proj.storyboard.assembled_at,
        )
    return ProjectDetailResponse(
        project_id=proj.project_id,
        title=proj.title,
        input_text=proj.input_text,
        status=proj.status,
        style_profile=proj.config.style_profile,
        image_model=proj.config.image_model,
        progress=_progress_to_response(proj.progress),
        storyboard=storyboard,
        thumbnail_url=proj.thumbnail_url,
        estimated_cost_usd=proj.estimated_cost_usd,
        error=proj.error,
        created_at=proj.created_at,
        updated_at=proj.updated_at,
    )


# ── Routes ────────────────────────────────────────────────────────

@router.post("", response_model=CreateProjectResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_project(
    body: CreateProjectRequest,
    background_tasks: BackgroundTasks,
    store: BaseStore = Depends(get_store),
    pipeline=Depends(get_pipeline),
    settings: Settings = Depends(get_settings),
):
    """
    Create a new storyboard project and start generation in the background.
    Returns immediately with project_id and polling URL.
    """
    config = GenerationConfig(
        image_model=body.options.image_model,
        style_profile=body.style_profile,
        max_panels=body.options.max_panels,
        image_quality=body.options.image_quality,
        detect_arc=body.options.detect_arc,
    )

    project = ProjectModel(
        title=body.title,
        input_text=body.input_text,
        config=config,
        status=ProjectStatus.QUEUED,
    )

    await store.create_project(project)

    # Ensure storage directory exists for this project
    project_storage = Path(settings.storage_path) / project.project_id
    project_storage.mkdir(parents=True, exist_ok=True)

    # Launch background pipeline — returns 202 immediately
    background_tasks.add_task(pipeline.run, project.project_id, config)

    return CreateProjectResponse(
        project_id=project.project_id,
        status=project.status,
        title=project.title,
        estimated_panels=config.max_panels,
        style_profile=config.style_profile,
        image_model=config.image_model,
        created_at=project.created_at,
        poll_url=f"/api/v1/projects/{project.project_id}/status",
    )


@router.get("", response_model=List[ProjectSummaryResponse])
async def list_projects(store: BaseStore = Depends(get_store)):
    """List all projects (newest first). No pagination needed for in-memory."""
    projects = await store.list_projects()
    result = []
    for proj in projects:
        completed = (
            sum(1 for p in proj.storyboard.panels if p.status == PanelStatus.DONE)
            if proj.storyboard else 0
        )
        total = len(proj.storyboard.panels) if proj.storyboard else proj.config.max_panels
        result.append(ProjectSummaryResponse(
            project_id=proj.project_id,
            title=proj.title,
            status=proj.status,
            style_profile=proj.config.style_profile,
            image_model=proj.config.image_model,
            total_panels=total,
            completed_panels=completed,
            thumbnail_url=proj.thumbnail_url,
            estimated_cost_usd=proj.estimated_cost_usd,
            created_at=proj.created_at,
            updated_at=proj.updated_at,
        ))
    return result


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(project_id: str, store: BaseStore = Depends(get_store)):
    """Full project detail including all storyboard panels."""
    proj = await store.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return _project_to_detail(proj)


@router.get("/{project_id}/status", response_model=StatusResponse)
async def get_project_status(project_id: str, store: BaseStore = Depends(get_store)):
    """
    Lightweight polling endpoint.
    Returns current status + only the panels that have completed so far.
    """
    proj = await store.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    completed_panels = []
    if proj.storyboard:
        completed_panels = [
            _panel_to_summary(p)
            for p in sorted(proj.storyboard.panels, key=lambda x: x.panel_index)
            if p.status in (PanelStatus.DONE, PanelStatus.FAILED)
        ]

    return StatusResponse(
        project_id=proj.project_id,
        status=proj.status,
        progress=_progress_to_response(proj.progress),
        completed_panels=completed_panels,
        error=proj.error,
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    store: BaseStore = Depends(get_store),
    settings: Settings = Depends(get_settings),
):
    """Delete project from memory and remove its image files."""
    proj = await store.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    # Remove local image files
    project_storage = Path(settings.storage_path) / project_id
    if project_storage.exists():
        shutil.rmtree(project_storage, ignore_errors=True)

    await store.delete_project(project_id)


@router.post("/{project_id}/regenerate", response_model=CreateProjectResponse, status_code=status.HTTP_202_ACCEPTED)
async def regenerate_project(
    project_id: str,
    body: RegenerateProjectRequest,
    background_tasks: BackgroundTasks,
    store: BaseStore = Depends(get_store),
    pipeline=Depends(get_pipeline),
    settings: Settings = Depends(get_settings),
):
    """Re-run the full pipeline on an existing project (keeps original text)."""
    proj = await store.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    # Apply any overrides from request body
    new_config = GenerationConfig(
        image_model=body.options.image_model if body.options else proj.config.image_model,
        style_profile=body.style_profile or proj.config.style_profile,
        max_panels=body.options.max_panels if body.options else proj.config.max_panels,
        image_quality=body.options.image_quality if body.options else proj.config.image_quality,
        detect_arc=body.options.detect_arc if body.options else proj.config.detect_arc,
    )

    # Reset project state
    await store.update_project(
        project_id,
        status=ProjectStatus.QUEUED,
        storyboard=None,
        thumbnail_url=None,
        error=None,
        config=new_config,
    )

    # Clean up old images
    project_storage = Path(settings.storage_path) / project_id
    if project_storage.exists():
        shutil.rmtree(project_storage, ignore_errors=True)
    project_storage.mkdir(parents=True, exist_ok=True)

    background_tasks.add_task(pipeline.run, project_id, new_config)

    return CreateProjectResponse(
        project_id=project_id,
        status=ProjectStatus.QUEUED,
        title=proj.title,
        estimated_panels=new_config.max_panels,
        style_profile=new_config.style_profile,
        image_model=new_config.image_model,
        created_at=proj.created_at,
        poll_url=f"/api/v1/projects/{project_id}/status",
    )