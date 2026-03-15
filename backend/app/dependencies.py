"""
FastAPI dependency injection.
All services are wired here and injected into route handlers.
Swapping a service (e.g. InMemoryStore → MongoStore) requires
changing exactly one line in this file.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import Depends, Request

from app.config import Settings, get_settings
from app.core.arc_detector import ArcDetectionService
from app.core.image_service import ImageServiceFactory
from app.core.pipeline import StoryboardPipeline
from app.core.prompt_engine import PromptEngineeringService
from app.core.segmentation import SegmentationService
from app.core.storyboard_builder import StoryboardBuilder
from app.core.style_engine import StyleEngine
from app.store.base import BaseStore


# ── Store ─────────────────────────────────────────────────────────
def get_store(request: Request) -> BaseStore:
    """Retrieve the shared store from app state."""
    return request.app.state.store


# ── Segmentation ──────────────────────────────────────────────────
@lru_cache(maxsize=1)
def get_segmentation_service() -> SegmentationService:
    settings = get_settings()
    return SegmentationService(
        min_panels=settings.min_panels,
        max_panels=settings.max_panels,
    )


# ── Arc Detector ──────────────────────────────────────────────────
@lru_cache(maxsize=1)
def get_arc_detector() -> ArcDetectionService:
    settings = get_settings()
    return ArcDetectionService(
        api_key=settings.anthropic_api_key,
        model=settings.claude_model,
    )


# ── Prompt Engine ─────────────────────────────────────────────────
@lru_cache(maxsize=1)
def get_prompt_engine() -> PromptEngineeringService:
    settings = get_settings()
    return PromptEngineeringService(
        api_key=settings.anthropic_api_key,
        model=settings.claude_model,
    )


# ── Style Engine ──────────────────────────────────────────────────
@lru_cache(maxsize=1)
def get_style_engine() -> StyleEngine:
    return StyleEngine()


# ── Image Service Factory ─────────────────────────────────────────
@lru_cache(maxsize=1)
def get_image_factory() -> ImageServiceFactory:
    settings = get_settings()
    return ImageServiceFactory(
        openai_api_key=settings.openai_api_key,
        google_api_key=settings.google_api_key,
        dalle_model=settings.dalle_model,
        dalle_size=settings.dalle_image_size,
        dalle_quality=settings.dalle_quality,
        gemini_model=settings.gemini_image_model,
        storage_path=settings.storage_path,
        static_url_prefix=settings.static_url_prefix,
    )


# ── Storyboard Builder ────────────────────────────────────────────
@lru_cache(maxsize=1)
def get_storyboard_builder() -> StoryboardBuilder:
    templates_dir = str(Path(__file__).parent / "templates")
    return StoryboardBuilder(templates_dir=templates_dir)


# ── Pipeline ──────────────────────────────────────────────────────
def get_pipeline(
    store: BaseStore = Depends(get_store),
    segmentation: SegmentationService = Depends(get_segmentation_service),
    arc_detector: ArcDetectionService = Depends(get_arc_detector),
    prompt_engine: PromptEngineeringService = Depends(get_prompt_engine),
    image_factory: ImageServiceFactory = Depends(get_image_factory),
    storyboard_builder: StoryboardBuilder = Depends(get_storyboard_builder),
    style_engine: StyleEngine = Depends(get_style_engine),
    settings: Settings = Depends(get_settings),
) -> StoryboardPipeline:
    return StoryboardPipeline(
        store=store,
        segmentation=segmentation,
        arc_detector=arc_detector,
        prompt_engine=prompt_engine,
        image_factory=image_factory,
        storyboard_builder=storyboard_builder,
        style_engine=style_engine,
        storage_path=settings.storage_path,
    )