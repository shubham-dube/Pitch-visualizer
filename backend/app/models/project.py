"""
Core domain models (Pydantic v2).
These represent the internal state of the application, not API shapes.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from app.models.enums import (
    ArcType,
    DominantEmotion,
    GenerationStage,
    ImageModel,
    PanelRole,
    PanelStatus,
    ProjectStatus,
    StyleProfile,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Segment (output of Stage 1) ────────────────────────────────────
class TextSegment(BaseModel):
    index: int
    text: str
    token_count: int
    is_merged: bool = False


# ── Arc Panel Meta (output of Stage 2) ────────────────────────────
class ArcPanelMeta(BaseModel):
    index: int
    role: PanelRole
    intensity: float = Field(ge=0.0, le=1.0)
    dominant_emotion: DominantEmotion


# ── Arc Detection Result (output of Stage 2) ──────────────────────
class ArcDetectionResult(BaseModel):
    overall_arc: ArcType
    panels: List[ArcPanelMeta]


# ── Generation Metadata per Panel ────────────────────────────────
class PanelGenerationMeta(BaseModel):
    model_used: ImageModel
    generation_time_ms: int = 0
    prompt_tokens: int = 0
    dalle_revised_prompt: Optional[str] = None
    retry_count: int = 0
    estimated_cost_usd: float = 0.0


# ── Individual Panel ──────────────────────────────────────────────
class PanelModel(BaseModel):
    panel_index: int
    scene_title: str = ""
    original_text: str
    engineered_prompt: str = ""
    visual_prompt: str = ""
    image_url: str = ""
    local_image_path: str = ""
    mood: str = ""
    dominant_emotion: DominantEmotion = DominantEmotion.NEUTRAL
    panel_role: PanelRole = PanelRole.CONTEXT
    intensity: float = 0.5
    color_palette: List[str] = Field(default_factory=list)
    key_elements: List[str] = Field(default_factory=list)
    generation_meta: PanelGenerationMeta = Field(
        default_factory=lambda: PanelGenerationMeta(model_used=ImageModel.DALLE3)
    )
    status: PanelStatus = PanelStatus.PENDING
    error: Optional[str] = None


# ── Storyboard ────────────────────────────────────────────────────
class StoryboardModel(BaseModel):
    panels: List[PanelModel] = Field(default_factory=list)
    overall_arc: ArcType = ArcType.INSPIRATIONAL
    html_export_path: Optional[str] = None
    assembled_at: Optional[datetime] = None


# ── Generation Config ─────────────────────────────────────────────
class GenerationConfig(BaseModel):
    image_model: ImageModel = ImageModel.DALLE3
    style_profile: StyleProfile = StyleProfile.CINEMATIC
    max_panels: int = 5
    image_quality: str = "hd"          # "standard" | "hd" (DALL-E only)
    detect_arc: bool = True


# ── Progress ──────────────────────────────────────────────────────
class ProgressModel(BaseModel):
    percent: int = 0
    current_stage: GenerationStage = GenerationStage.SEGMENTING
    completed_panels: int = 0
    total_panels: int = 0
    elapsed_seconds: float = 0.0
    estimated_remaining_seconds: Optional[float] = None


# ── Project (top-level entity) ────────────────────────────────────
class ProjectModel(BaseModel):
    project_id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    input_text: str
    config: GenerationConfig
    status: ProjectStatus = ProjectStatus.QUEUED
    storyboard: Optional[StoryboardModel] = None
    progress: ProgressModel = Field(default_factory=ProgressModel)
    thumbnail_url: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    def touch(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = _utcnow()

    @property
    def panel_count(self) -> int:
        if self.storyboard:
            return len(self.storyboard.panels)
        return 0

    @property
    def estimated_cost_usd(self) -> float:
        if not self.storyboard:
            return 0.0
        return sum(
            p.generation_meta.estimated_cost_usd
            for p in self.storyboard.panels
        )