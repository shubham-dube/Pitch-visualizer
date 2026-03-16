"""
Stage 5 — Image Generation.

Supports two backends:
  - DALL-E 3  (OpenAI)
  - Gemini-3.1-flash-image-preview  (Google Gemini)

Both implement the same interface: generate(prompt) -> local_file_path.
Selection is driven by ImageModel enum passed in GenerationConfig.
"""
from __future__ import annotations

import asyncio
import os
import time
import uuid
from pathlib import Path
from typing import Optional

import aiohttp

from app.models.enums import ImageModel, StyleProfile
from app.utils.cost_estimator import estimate_dalle_cost, estimate_gemini_image_cost
from app.utils.errors import ContentPolicyError, ImageGenerationError, RateLimitError
from app.utils.logger import get_logger

logger = get_logger(__name__)

_MAX_RETRIES = 3
_RETRY_DELAYS = [1.0, 2.0, 4.0]   # exponential backoff seconds


# ── Shared download helper ────────────────────────────────────────

async def _download_image(url: str, dest_path: Path) -> None:
    """Download an image from a URL and save to dest_path."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
            resp.raise_for_status()
            content = await resp.read()
    dest_path.write_bytes(content)


# ── DALL-E 3 Backend ──────────────────────────────────────────────

class DalleImageService:
    """Generates images via OpenAI DALL-E 3."""

    def __init__(
        self,
        api_key: str,
        model: str = "dall-e-3",
        image_size: str = "1792x1024",
        quality: str = "hd",
        storage_path: str = "./storage/images",
        static_url_prefix: str = "/static/images",
    ) -> None:
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        self._size = image_size
        self._quality = quality
        self._storage_path = Path(storage_path)
        self._static_url_prefix = static_url_prefix

    async def generate(
        self,
        visual_prompt: str,
        project_id: str,
        panel_index: int,
        dalle_style: str = "vivid",
    ) -> dict:
        """
        Returns:
            {
                local_path: str,
                served_url: str,
                revised_prompt: str,
                generation_time_ms: int,
                estimated_cost_usd: float,
                retry_count: int,
            }
        """
        last_error: Optional[Exception] = None

        for attempt in range(_MAX_RETRIES):
            try:
                start = time.monotonic()

                response = await self._client.images.generate(
                    model=self._model,
                    prompt=visual_prompt,
                    n=1,
                    size=self._size,
                    quality=self._quality,
                    style=dalle_style,
                    response_format="url",
                )

                elapsed_ms = int((time.monotonic() - start) * 1000)
                image_data = response.data[0]
                image_url = image_data.url
                revised_prompt = getattr(image_data, "revised_prompt", None) or visual_prompt

                # Download and store locally
                filename = f"panel_{panel_index}.png"
                project_dir = self._storage_path / project_id
                dest_path = project_dir / filename
                await _download_image(image_url, dest_path)

                served_url = f"{self._static_url_prefix}/{project_id}/{filename}"

                logger.info(
                    "DALL-E image generated",
                    panel_index=panel_index,
                    elapsed_ms=elapsed_ms,
                    attempt=attempt + 1,
                )

                return {
                    "local_path": str(dest_path),
                    "served_url": served_url,
                    "revised_prompt": revised_prompt,
                    "generation_time_ms": elapsed_ms,
                    "estimated_cost_usd": estimate_dalle_cost(self._quality),
                    "retry_count": attempt,
                }

            except Exception as exc:
                last_error = exc
                error_str = str(exc).lower()

                # Content policy — do NOT retry
                if "content_policy" in error_str or "safety" in error_str:
                    raise ContentPolicyError(
                        f"DALL-E content policy violation on panel {panel_index}.",
                        detail={"panel_index": panel_index, "prompt_snippet": visual_prompt[:120]},
                    ) from exc

                # Rate limit — wait longer
                if "rate_limit" in error_str or "429" in error_str:
                    wait = _RETRY_DELAYS[min(attempt, len(_RETRY_DELAYS) - 1)] * 3
                    logger.warning("DALL-E rate limit, backing off", wait=wait, attempt=attempt + 1)
                    await asyncio.sleep(wait)
                    continue

                if attempt < _MAX_RETRIES - 1:
                    wait = _RETRY_DELAYS[attempt]
                    logger.warning(
                        "DALL-E generation failed, retrying",
                        error=str(exc),
                        attempt=attempt + 1,
                        wait=wait,
                    )
                    await asyncio.sleep(wait)

        raise ImageGenerationError(
            f"DALL-E generation failed after {_MAX_RETRIES} attempts for panel {panel_index}.",
            detail={"panel_index": panel_index, "last_error": str(last_error)},
        ) from last_error


# ── Gemini Imagen Backend ─────────────────────────────────────────

class GeminiImageService:
    """Generates images via Google Gemini Imagen 3."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.1-flash-image-preview",
        storage_path: str = "./storage/images",
        static_url_prefix: str = "/static/images",
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._storage_path = Path(storage_path)
        self._static_url_prefix = static_url_prefix

    async def generate(
        self,
        visual_prompt: str,
        project_id: str,
        panel_index: int,
        style_hint: str = "",
    ) -> dict:
        """
        Returns same shape as DalleImageService.generate().
        """
        last_error: Optional[Exception] = None

        full_prompt = f"{visual_prompt}"
        if style_hint:
            full_prompt = f"{visual_prompt.rstrip('.')}. {style_hint}"

        for attempt in range(_MAX_RETRIES):
            try:
                start = time.monotonic()

                # Run sync Gemini SDK in thread executor
                loop = asyncio.get_event_loop()
                image_bytes = await loop.run_in_executor(
                    None,
                    lambda: self._generate_sync(full_prompt),
                )

                elapsed_ms = int((time.monotonic() - start) * 1000)

                # Save to local storage
                filename = f"panel_{panel_index}.png"
                project_dir = self._storage_path / project_id
                project_dir.mkdir(parents=True, exist_ok=True)
                dest_path = project_dir / filename
                dest_path.write_bytes(image_bytes)

                served_url = f"{self._static_url_prefix}/{project_id}/{filename}"

                logger.info(
                    "Gemini image generated",
                    panel_index=panel_index,
                    elapsed_ms=elapsed_ms,
                    attempt=attempt + 1,
                )

                return {
                    "local_path": str(dest_path),
                    "served_url": served_url,
                    "revised_prompt": full_prompt,
                    "generation_time_ms": elapsed_ms,
                    "estimated_cost_usd": estimate_gemini_image_cost(),
                    "retry_count": attempt,
                }

            except Exception as exc:
                last_error = exc
                error_str = str(exc).lower()

                if "safety" in error_str or "blocked" in error_str:
                    raise ContentPolicyError(
                        f"Gemini safety filter blocked panel {panel_index}.",
                        detail={"panel_index": panel_index},
                    ) from exc

                if "quota" in error_str or "429" in error_str:
                    wait = _RETRY_DELAYS[min(attempt, len(_RETRY_DELAYS) - 1)] * 3
                    logger.warning("Gemini quota hit, backing off", wait=wait)
                    await asyncio.sleep(wait)
                    continue

                if attempt < _MAX_RETRIES - 1:
                    wait = _RETRY_DELAYS[attempt]
                    logger.warning("Gemini generation failed, retrying", error=str(exc), attempt=attempt + 1)
                    await asyncio.sleep(wait)

        raise ImageGenerationError(
            f"Gemini generation failed after {_MAX_RETRIES} attempts for panel {panel_index}.",
            detail={"panel_index": panel_index, "last_error": str(last_error)},
        ) from last_error

    def _generate_sync(self, prompt: str) -> bytes:
        """Synchronous Gemini API call — runs in thread executor."""
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self._api_key)

        response = client.models.generate_content(
            model=self._model,  # e.g. "gemini-3.1-flash-image-preview"
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)],
                )
            ],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    image_size="1K",
                    aspect_ratio="16:9",
                ),
            ),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data:
                return part.inline_data.data

        raise ImageGenerationError("Gemini returned no images.")


# ── Factory ───────────────────────────────────────────────────────

class ImageServiceFactory:
    """
    Returns the correct image generation service based on ImageModel enum.
    Centralises all configuration so the pipeline just calls .generate().
    """

    def __init__(
        self,
        openai_api_key: str,
        google_api_key: str,
        dalle_model: str,
        dalle_size: str,
        dalle_quality: str,
        gemini_model: str,
        storage_path: str,
        static_url_prefix: str,
    ) -> None:
        self._openai_key = openai_api_key
        self._google_key = google_api_key
        self._dalle_model = dalle_model
        self._dalle_size = dalle_size
        self._dalle_quality = dalle_quality
        self._gemini_model = gemini_model
        self._storage_path = storage_path
        self._static_url_prefix = static_url_prefix

        # Lazily instantiated
        self._dalle: Optional[DalleImageService] = None
        self._gemini: Optional[GeminiImageService] = None

    def get(self, model: ImageModel) -> DalleImageService | GeminiImageService:
        if model == ImageModel.DALLE3:
            if self._dalle is None:
                self._dalle = DalleImageService(
                    api_key=self._openai_key,
                    model=self._dalle_model,
                    image_size=self._dalle_size,
                    quality=self._dalle_quality,
                    storage_path=self._storage_path,
                    static_url_prefix=self._static_url_prefix,
                )
            return self._dalle

        if model == ImageModel.GEMINI:
            if self._gemini is None:
                self._gemini = GeminiImageService(
                    api_key=self._google_key,
                    model=self._gemini_model,
                    storage_path=self._storage_path,
                    static_url_prefix=self._static_url_prefix,
                )
            return self._gemini

        raise ValueError(f"Unknown ImageModel: {model}")