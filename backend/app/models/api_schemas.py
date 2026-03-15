"""
API-facing Pydantic schemas (request bodies & response shapes).
Kept separate from domain models for clean separation of concerns.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

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


# ── Requests ──────────────────────────────────────────────────────

class GenerationOptionsRequest(BaseModel):
    max_panels: int = Field(default=5, ge=3, le=8)
    image_quality: str = Field(default="hd", pattern="^(standard|hd)$")
    detect_arc: bool = True
    image_model: ImageModel = ImageModel.DALLE3


class CreateProjectRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Project title")
    input_text: str = Field(
        ...,
        min_length=50,
        max_length=5000,
        description="Narrative text to visualise (min 50 chars)",
    )
    style_profile: StyleProfile = StyleProfile.CINEMATIC
    options: GenerationOptionsRequest = Field(default_factory=GenerationOptionsRequest)

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        return v.strip()

    @field_validator("input_text")
    @classmethod
    def strip_text(cls, v: str) -> str:
        return v.strip()


class RegenerateProjectRequest(BaseModel):
    style_profile: Optional[StyleProfile] = None
    options: Optional[GenerationOptionsRequest] = None


class RegeneratePanelRequest(BaseModel):
    prompt_override: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Custom visual prompt. If omitted, re-runs the full prompt pipeline.",
    )
    image_model: Optional[ImageModel] = None


class UpdatePanelPromptRequest(BaseModel):
    engineered_prompt: str = Field(..., min_length=10, max_length=1000)


class PreviewPromptRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=1000)
    style_profile: StyleProfile = StyleProfile.CINEMATIC
    panel_role: PanelRole = PanelRole.CONTEXT
    intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    dominant_emotion: DominantEmotion = DominantEmotion.NEUTRAL


# ── Response sub-objects ──────────────────────────────────────────

class ColorPaletteItem(BaseModel):
    hex: str


class PanelSummaryResponse(BaseModel):
    """Lightweight panel used in status polling responses."""
    panel_index: int
    scene_title: str
    image_url: str
    mood: str
    panel_role: PanelRole
    dominant_emotion: DominantEmotion
    intensity: float
    color_palette: List[str]
    status: PanelStatus
    error: Optional[str] = None


class PanelDetailResponse(BaseModel):
    """Full panel detail for storyboard viewer."""
    panel_index: int
    scene_title: str
    original_text: str
    engineered_prompt: str
    visual_prompt: str
    image_url: str
    mood: str
    panel_role: PanelRole
    dominant_emotion: DominantEmotion
    intensity: float
    color_palette: List[str]
    key_elements: List[str]
    dalle_revised_prompt: Optional[str]
    generation_time_ms: int
    estimated_cost_usd: float
    model_used: ImageModel
    retry_count: int
    status: PanelStatus
    error: Optional[str] = None


class ProgressResponse(BaseModel):
    percent: int
    current_stage: GenerationStage
    completed_panels: int
    total_panels: int
    elapsed_seconds: float
    estimated_remaining_seconds: Optional[float]


class StoryboardResponse(BaseModel):
    overall_arc: ArcType
    panels: List[PanelDetailResponse]
    assembled_at: Optional[datetime]


class ProjectSummaryResponse(BaseModel):
    """Used in list endpoints — no full panel data."""
    project_id: str
    title: str
    status: ProjectStatus
    style_profile: StyleProfile
    image_model: ImageModel
    total_panels: int
    completed_panels: int
    thumbnail_url: Optional[str]
    estimated_cost_usd: float
    created_at: datetime
    updated_at: datetime


class ProjectDetailResponse(BaseModel):
    """Full project — returned by GET /projects/{id}."""
    project_id: str
    title: str
    input_text: str
    status: ProjectStatus
    style_profile: StyleProfile
    image_model: ImageModel
    progress: ProgressResponse
    storyboard: Optional[StoryboardResponse]
    thumbnail_url: Optional[str]
    estimated_cost_usd: float
    error: Optional[str]
    created_at: datetime
    updated_at: datetime


class StatusResponse(BaseModel):
    """Lightweight polling endpoint response."""
    project_id: str
    status: ProjectStatus
    progress: ProgressResponse
    completed_panels: List[PanelSummaryResponse]
    error: Optional[str] = None


class CreateProjectResponse(BaseModel):
    project_id: str
    status: ProjectStatus
    title: str
    estimated_panels: int
    style_profile: StyleProfile
    image_model: ImageModel
    created_at: datetime
    poll_url: str


class StyleProfileInfo(BaseModel):
    id: StyleProfile
    display_name: str
    description: str
    visual_vibe: str
    best_for: str


class ImageModelInfo(BaseModel):
    id: ImageModel
    display_name: str
    description: str
    image_size: str
    speed: str
    quality: str


class PreviewPromptResponse(BaseModel):
    scene_title: str
    visual_prompt: str
    mood: str
    color_palette: List[str]
    key_elements: List[str]


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    project_count: int
    uptime_seconds: float


class ErrorResponse(BaseModel):
    error: str
    message: str
    detail: Optional[dict] = None
    timestamp: datetime