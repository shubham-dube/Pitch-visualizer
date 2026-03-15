"""
Panels API — v1.

POST  /projects/{id}/panels/{idx}/regenerate   Regenerate one panel
PATCH /projects/{id}/panels/{idx}/prompt       Update prompt only
POST  /api/v1/preview-prompt                   Preview prompt (no image gen)
"""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.config import Settings, get_settings
from app.core.image_service import ImageServiceFactory
from app.core.prompt_engine import PromptEngineeringService
from app.core.style_engine import StyleEngine
from app.dependencies import get_image_factory, get_pipeline, get_prompt_engine, get_store, get_style_engine
from app.models.api_schemas import (
    PanelDetailResponse,
    PreviewPromptRequest,
    PreviewPromptResponse,
    RegeneratePanelRequest,
    UpdatePanelPromptRequest,
)
from app.models.enums import ArcType, ImageModel, PanelStatus
from app.models.project import (
    ArcDetectionResult,
    ArcPanelMeta,
    GenerationConfig,
    PanelGenerationMeta,
    PanelModel,
    TextSegment,
)
from app.store.base import BaseStore

router = APIRouter(tags=["Panels"])


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


async def _run_single_panel_regen(
    project_id: str,
    panel_index: int,
    store: BaseStore,
    pipeline,
    prompt_override: str | None,
    image_model_override: ImageModel | None,
    settings: Settings,
) -> None:
    """Background task: regenerates a single panel in-place."""
    proj = await store.get_project(project_id)
    if not proj or not proj.storyboard:
        return

    # Find the panel
    existing = next(
        (p for p in proj.storyboard.panels if p.panel_index == panel_index), None
    )
    if not existing:
        return

    image_model = image_model_override or proj.config.image_model
    style_profile = proj.config.style_profile

    # Mark as generating
    await store.upsert_panel(project_id, PanelModel(
        **{**existing.model_dump(), "status": PanelStatus.GENERATING, "error": None}
    ))

    try:
        if prompt_override:
            visual_prompt = prompt_override
            engineered_prompt = prompt_override
            scene_title = existing.scene_title
            mood = existing.mood
            key_elements = existing.key_elements
            prompt_tokens = 0
        else:
            # Re-run prompt engineering
            fake_segment = TextSegment(
                index=panel_index,
                text=existing.original_text,
                token_count=len(existing.original_text.split()),
            )
            fake_arc = ArcDetectionResult(
                overall_arc=proj.storyboard.overall_arc,
                panels=[ArcPanelMeta(
                    index=panel_index,
                    role=existing.panel_role,
                    intensity=existing.intensity,
                    dominant_emotion=existing.dominant_emotion,
                )],
            )
            prompt_data = await pipeline._prompt_engine.engineer_prompt(
                segment=fake_segment,
                arc_result=fake_arc,
                style_profile=style_profile,
                total_panels=len(proj.storyboard.panels),
            )
            visual_prompt = prompt_data["visual_prompt"]
            engineered_prompt = prompt_data["engineered_prompt"]
            scene_title = prompt_data["scene_title"]
            mood = prompt_data["mood"]
            key_elements = prompt_data.get("key_elements", [])
            prompt_tokens = prompt_data.get("prompt_tokens", 0)

        # Generate image
        image_service = pipeline._image_factory.get(image_model)
        style_config = pipeline._style_engine.get_config(style_profile)

        if image_model == ImageModel.DALLE3:
            image_result = await image_service.generate(
                visual_prompt=visual_prompt,
                project_id=project_id,
                panel_index=panel_index,
                dalle_style=style_config.dalle_style,
            )
        else:
            image_result = await image_service.generate(
                visual_prompt=visual_prompt,
                project_id=project_id,
                panel_index=panel_index,
                style_hint=style_config.gemini_style_hint,
            )

        updated_panel = PanelModel(
            panel_index=panel_index,
            scene_title=scene_title,
            original_text=existing.original_text,
            engineered_prompt=engineered_prompt,
            visual_prompt=visual_prompt,
            image_url=image_result["served_url"],
            local_image_path=image_result["local_path"],
            mood=mood,
            dominant_emotion=existing.dominant_emotion,
            panel_role=existing.panel_role,
            intensity=existing.intensity,
            color_palette=existing.color_palette,
            key_elements=key_elements,
            generation_meta=PanelGenerationMeta(
                model_used=image_model,
                generation_time_ms=image_result["generation_time_ms"],
                prompt_tokens=prompt_tokens,
                dalle_revised_prompt=image_result.get("revised_prompt"),
                retry_count=image_result.get("retry_count", 0),
                estimated_cost_usd=image_result["estimated_cost_usd"],
            ),
            status=PanelStatus.DONE,
        )

    except Exception as exc:
        updated_panel = PanelModel(
            **{**existing.model_dump(), "status": PanelStatus.FAILED, "error": str(exc)}
        )

    await store.upsert_panel(project_id, updated_panel)


@router.post("/projects/{project_id}/panels/{panel_index}/regenerate", response_model=dict)
async def regenerate_panel(
    project_id: str,
    panel_index: int,
    body: RegeneratePanelRequest,
    background_tasks: BackgroundTasks,
    store: BaseStore = Depends(get_store),
    pipeline=Depends(get_pipeline),
    settings: Settings = Depends(get_settings),
):
    """Regenerate a single panel. Accepts optional prompt override."""
    proj = await store.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")
    if not proj.storyboard:
        raise HTTPException(status_code=400, detail="Storyboard not generated yet.")

    panel_exists = any(p.panel_index == panel_index for p in proj.storyboard.panels)
    if not panel_exists:
        raise HTTPException(status_code=404, detail=f"Panel {panel_index} not found.")

    background_tasks.add_task(
        _run_single_panel_regen,
        project_id=project_id,
        panel_index=panel_index,
        store=store,
        pipeline=pipeline,
        prompt_override=body.prompt_override,
        image_model_override=body.image_model,
        settings=settings,
    )

    return {
        "message": f"Panel {panel_index} regeneration started.",
        "project_id": project_id,
        "panel_index": panel_index,
        "poll_url": f"/api/v1/projects/{project_id}/status",
    }


@router.patch("/projects/{project_id}/panels/{panel_index}/prompt", response_model=PanelDetailResponse)
async def update_panel_prompt(
    project_id: str,
    panel_index: int,
    body: UpdatePanelPromptRequest,
    store: BaseStore = Depends(get_store),
):
    """Update a panel's engineered prompt without regenerating the image."""
    proj = await store.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")
    if not proj.storyboard:
        raise HTTPException(status_code=400, detail="Storyboard not generated yet.")

    panel = next((p for p in proj.storyboard.panels if p.panel_index == panel_index), None)
    if not panel:
        raise HTTPException(status_code=404, detail=f"Panel {panel_index} not found.")

    # Patch just the prompt fields
    updated = PanelModel(**{**panel.model_dump(), "engineered_prompt": body.engineered_prompt})
    await store.upsert_panel(project_id, updated)

    return _panel_to_detail(updated)


@router.post("/preview-prompt", response_model=PreviewPromptResponse)
async def preview_prompt(
    body: PreviewPromptRequest,
    prompt_engine: PromptEngineeringService = Depends(get_prompt_engine),
):
    """
    Generate a visual prompt preview using Claude without calling the image API.
    Used by the frontend panel editor 'Preview' button.
    """
    result = await prompt_engine.preview_prompt(
        text=body.text,
        style_profile=body.style_profile,
        panel_role=body.panel_role,
        intensity=body.intensity,
        dominant_emotion=body.dominant_emotion,
    )
    return PreviewPromptResponse(
        scene_title=result["scene_title"],
        visual_prompt=result["visual_prompt"],
        mood=result["mood"],
        color_palette=[],
        key_elements=result.get("key_elements", []),
    )