"""
Styles & Models API — v1.

GET /styles        All available style profiles
GET /models        All available image generation models
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends

from app.dependencies import get_style_engine
from app.models.api_schemas import ImageModelInfo, StyleProfileInfo
from app.models.enums import ImageModel, StyleProfile

router = APIRouter(tags=["Config"])


@router.get("/styles", response_model=List[StyleProfileInfo])
async def list_styles(style_engine=Depends(get_style_engine)):
    """Return all available style profiles with metadata."""
    profiles = []
    for profile, config in style_engine.all_profiles().items():
        profiles.append(StyleProfileInfo(
            id=profile,
            display_name=config.display_name,
            description=config.description,
            visual_vibe=config.visual_vibe,
            best_for=config.best_for,
        ))
    return profiles


@router.get("/models", response_model=List[ImageModelInfo])
async def list_models():
    """Return all available image generation models."""
    return [
        ImageModelInfo(
            id=ImageModel.DALLE3,
            display_name="DALL-E 3 (OpenAI)",
            description="OpenAI's most capable image model. Exceptional prompt adherence and detail.",
            image_size="1792×1024 (16:9 widescreen)",
            speed="~15–25s per image",
            quality="Excellent — HD mode produces stunning results",
        ),
        ImageModelInfo(
            id=ImageModel.GEMINI,
            display_name="Imagen 3 (Google Gemini)",
            description="Google's latest image generation model. Photorealistic and highly detailed.",
            image_size="16:9 aspect ratio",
            speed="~10–20s per image",
            quality="Excellent — photorealistic quality with strong prompt following",
        ),
    ]