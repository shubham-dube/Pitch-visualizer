"""
Master Pipeline Orchestrator.

Coordinates all 6 stages of storyboard generation:
  1. Text Segmentation
  2. Narrative Arc Detection
  3. Prompt Engineering (per panel, via Claude)
  4. Style Application
  5. Image Generation (DALL-E 3 or Gemini, parallel)
  6. Storyboard Assembly

Updates the in-memory store after every panel so the frontend
gets live progress via the /status polling endpoint.
"""
from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import List, Optional

from app.core.arc_detector import ArcDetectionService
from app.core.image_service import ContentPolicyError, ImageGenerationError, ImageServiceFactory
from app.core.prompt_engine import PromptEngineeringService
from app.core.segmentation import SegmentationService
from app.core.storyboard_builder import StoryboardBuilder
from app.core.style_engine import StyleEngine
from app.models.enums import GenerationStage, ImageModel, PanelStatus, ProjectStatus
from app.models.project import (
    GenerationConfig,
    PanelGenerationMeta,
    PanelModel,
    ProgressModel,
    StoryboardModel,
    TextSegment,
)
from app.store.base import BaseStore
from app.utils.errors import SegmentationError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class StoryboardPipeline:
    """
    Runs the full generation pipeline for a single project.
    Designed to run as a FastAPI BackgroundTask.
    """

    def __init__(
        self,
        store: BaseStore,
        segmentation: SegmentationService,
        arc_detector: ArcDetectionService,
        prompt_engine: PromptEngineeringService,
        image_factory: ImageServiceFactory,
        storyboard_builder: StoryboardBuilder,
        style_engine: StyleEngine,
        storage_path: str,
    ) -> None:
        self._store = store
        self._segmentation = segmentation
        self._arc_detector = arc_detector
        self._prompt_engine = prompt_engine
        self._image_factory = image_factory
        self._builder = storyboard_builder
        self._style_engine = style_engine
        self._storage_path = Path(storage_path)

    # ── Public entry point ────────────────────────────────────────

    async def run(self, project_id: str, config: GenerationConfig) -> None:
        """
        Full pipeline. Called as a background task.
        All errors are caught and stored — never propagated to caller.
        """
        start_time = time.monotonic()
        logger.info("Pipeline started", project_id=project_id, config=config.model_dump())

        try:
            await self._run_pipeline(project_id, config, start_time)
        except Exception as exc:
            logger.error("Pipeline fatal error", project_id=project_id, error=str(exc), exc_info=True)
            await self._store.update_project(
                project_id,
                status=ProjectStatus.FAILED,
                error=str(exc),
            )

    # ── Internal pipeline ─────────────────────────────────────────

    async def _run_pipeline(
        self, project_id: str, config: GenerationConfig, start_time: float
    ) -> None:

        project = await self._store.get_project(project_id)
        if not project:
            raise RuntimeError(f"Project {project_id} not found at pipeline start.")

        # ── Stage 1: Segmentation ─────────────────────────────────
        await self._update_progress(project_id, GenerationStage.SEGMENTING, 0, 0, 0, start_time)
        await self._store.update_project(project_id, status=ProjectStatus.GENERATING)

        segments = self._segmentation.segment(
            text=project.input_text,
            desired_panels=config.max_panels,
        )
        total = len(segments)
        logger.info("Segments created", count=total)

        # Initialise pending panels in store
        for seg in segments:
            panel = PanelModel(
                panel_index=seg.index,
                original_text=seg.text,
                status=PanelStatus.PENDING,
                generation_meta=PanelGenerationMeta(model_used=config.image_model),
            )
            await self._store.upsert_panel(project_id, panel)

        await self._store.update_project(project_id, progress=ProgressModel(
            percent=5,
            current_stage=GenerationStage.ARC_DETECTION,
            completed_panels=0,
            total_panels=total,
            elapsed_seconds=time.monotonic() - start_time,
        ))

        # ── Stage 2: Arc Detection ────────────────────────────────
        await self._update_progress(project_id, GenerationStage.ARC_DETECTION, 5, 0, total, start_time)

        if config.detect_arc:
            arc_result = await self._arc_detector.detect(segments)
        else:
            from app.core.arc_detector import _default_arc
            arc_result = _default_arc(len(segments))

        await self._store.update_project(project_id, progress=ProgressModel(
            percent=10,
            current_stage=GenerationStage.PROMPT_ENGINEERING,
            completed_panels=0,
            total_panels=total,
            elapsed_seconds=time.monotonic() - start_time,
        ))

        # ── Stages 3-5: Prompt + Image per panel (parallel) ───────
        await self._update_progress(project_id, GenerationStage.PROMPT_ENGINEERING, 12, 0, total, start_time)

        # Generate all panels concurrently with asyncio.gather
        tasks = [
            self._generate_panel(
                project_id=project_id,
                segment=seg,
                arc_result=arc_result,
                config=config,
                total=total,
                start_time=start_time,
            )
            for seg in segments
        ]
        panels: List[PanelModel] = await asyncio.gather(*tasks)

        # ── Stage 6: Assembly ─────────────────────────────────────
        await self._update_progress(project_id, GenerationStage.ASSEMBLING, 95, total, total, start_time)

        # Generate HTML export
        export_path = self._storage_path / project_id / "storyboard.html"
        completed_panels = [p for p in panels if p.status == PanelStatus.DONE]
        storyboard = self._builder.assemble(
            panels=panels,
            overall_arc=arc_result.overall_arc,
        )

        if completed_panels:
            self._builder.generate_html_export(
                storyboard=storyboard,
                title=project.title,
                style_profile=config.style_profile,
                export_path=export_path,
            )
            storyboard.html_export_path = str(export_path)

        # Set thumbnail to first completed panel
        thumbnail = next(
            (p.image_url for p in sorted(panels, key=lambda x: x.panel_index)
             if p.image_url), None
        )

        elapsed = time.monotonic() - start_time
        await self._store.update_project(
            project_id,
            status=ProjectStatus.COMPLETED,
            storyboard=storyboard,
            thumbnail_url=thumbnail,
            progress=ProgressModel(
                percent=100,
                current_stage=GenerationStage.DONE,
                completed_panels=len(completed_panels),
                total_panels=total,
                elapsed_seconds=elapsed,
            ),
        )

        logger.info(
            "Pipeline completed",
            project_id=project_id,
            total_panels=total,
            completed=len(completed_panels),
            elapsed_s=round(elapsed, 1),
        )

    # ── Per-panel generation ──────────────────────────────────────

    async def _generate_panel(
        self,
        project_id: str,
        segment: TextSegment,
        arc_result,
        config: GenerationConfig,
        total: int,
        start_time: float,
    ) -> PanelModel:
        """
        Runs Stage 3 (prompt) + Stage 4 (style) + Stage 5 (image) for one panel.
        Updates store on every state change so the frontend sees live progress.
        """
        panel_meta = arc_result.panels[segment.index]
        style_config = self._style_engine.get_config(config.style_profile)

        # Mark as generating
        panel = PanelModel(
            panel_index=segment.index,
            original_text=segment.text,
            panel_role=panel_meta.role,
            dominant_emotion=panel_meta.dominant_emotion,
            intensity=panel_meta.intensity,
            status=PanelStatus.GENERATING,
            generation_meta=PanelGenerationMeta(model_used=config.image_model),
        )
        await self._store.upsert_panel(project_id, panel)

        try:
            # Stage 3: Prompt Engineering
            prev_title = await self._get_prev_panel_title(project_id, segment.index)
            prompt_data = await self._prompt_engine.engineer_prompt(
                segment=segment,
                arc_result=arc_result,
                style_profile=config.style_profile,
                prev_title=prev_title,
                total_panels=total,
            )

            # Stage 4: Color palette from style engine
            color_palette = self._style_engine.get_color_palette(
                config.style_profile, panel_meta.dominant_emotion.value
            )

            # Stage 5: Image generation
            image_service = self._image_factory.get(config.image_model)

            if config.image_model == ImageModel.DALLE3:
                image_result = await image_service.generate(
                    visual_prompt=prompt_data["visual_prompt"],
                    project_id=project_id,
                    panel_index=segment.index,
                    dalle_style=style_config.dalle_style,
                )
            else:
                image_result = await image_service.generate(
                    visual_prompt=prompt_data["visual_prompt"],
                    project_id=project_id,
                    panel_index=segment.index,
                    style_hint=style_config.gemini_style_hint,
                )

            # Assemble completed panel
            panel = PanelModel(
                panel_index=segment.index,
                scene_title=prompt_data["scene_title"],
                original_text=segment.text,
                engineered_prompt=prompt_data["engineered_prompt"],
                visual_prompt=prompt_data["visual_prompt"],
                image_url=image_result["served_url"],
                local_image_path=image_result["local_path"],
                mood=prompt_data["mood"],
                dominant_emotion=panel_meta.dominant_emotion,
                panel_role=panel_meta.role,
                intensity=panel_meta.intensity,
                color_palette=color_palette,
                key_elements=prompt_data.get("key_elements", []),
                generation_meta=PanelGenerationMeta(
                    model_used=config.image_model,
                    generation_time_ms=image_result["generation_time_ms"],
                    prompt_tokens=prompt_data.get("prompt_tokens", 0),
                    dalle_revised_prompt=image_result.get("revised_prompt"),
                    retry_count=image_result.get("retry_count", 0),
                    estimated_cost_usd=image_result["estimated_cost_usd"],
                ),
                status=PanelStatus.DONE,
            )

        except ContentPolicyError as exc:
            logger.warning("Content policy on panel, using placeholder", panel=segment.index, error=str(exc))
            panel = self._failed_panel(segment, panel_meta, config.image_model, str(exc))

        except Exception as exc:
            logger.error("Panel generation failed", panel=segment.index, error=str(exc), exc_info=True)
            panel = self._failed_panel(segment, panel_meta, config.image_model, str(exc))

        await self._store.upsert_panel(project_id, panel)

        # Update project-level progress
        proj = await self._store.get_project(project_id)
        if proj and proj.storyboard:
            done_count = sum(
                1 for p in proj.storyboard.panels if p.status == PanelStatus.DONE
            )
            percent = 12 + int((done_count / total) * 83)  # 12%→95% range for images
            elapsed = time.monotonic() - start_time
            eta = (elapsed / done_count * (total - done_count)) if done_count > 0 else None
            await self._store.update_project(
                project_id,
                progress=ProgressModel(
                    percent=percent,
                    current_stage=GenerationStage.IMAGE_GENERATION,
                    completed_panels=done_count,
                    total_panels=total,
                    elapsed_seconds=elapsed,
                    estimated_remaining_seconds=eta,
                ),
            )

        return panel

    # ── Helpers ───────────────────────────────────────────────────

    async def _get_prev_panel_title(
        self, project_id: str, current_index: int
    ) -> Optional[str]:
        if current_index == 0:
            return None
        proj = await self._store.get_project(project_id)
        if not proj or not proj.storyboard:
            return None
        for p in proj.storyboard.panels:
            if p.panel_index == current_index - 1 and p.scene_title:
                return p.scene_title
        return None

    async def _update_progress(
        self,
        project_id: str,
        stage: GenerationStage,
        percent: int,
        completed: int,
        total: int,
        start_time: float,
    ) -> None:
        await self._store.update_project(
            project_id,
            progress=ProgressModel(
                percent=percent,
                current_stage=stage,
                completed_panels=completed,
                total_panels=total,
                elapsed_seconds=time.monotonic() - start_time,
            ),
        )

    @staticmethod
    def _failed_panel(
        segment: TextSegment, panel_meta, image_model: ImageModel, error: str
    ) -> PanelModel:
        return PanelModel(
            panel_index=segment.index,
            scene_title=f"Panel {segment.index + 1}",
            original_text=segment.text,
            panel_role=panel_meta.role,
            dominant_emotion=panel_meta.dominant_emotion,
            intensity=panel_meta.intensity,
            generation_meta=PanelGenerationMeta(model_used=image_model),
            status=PanelStatus.FAILED,
            error=error,
        )