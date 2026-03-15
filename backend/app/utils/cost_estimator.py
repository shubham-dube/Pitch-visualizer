"""
Cost estimation utilities based on Anthropic pricing table.
All token prices are per 1M tokens (MTok).
"""

from __future__ import annotations
from app.models.enums import ImageModel


# ── Claude Sonnet 4.5 pricing (USD) ──────────────────────────────
_CLAUDE_INPUT_COST_PER_MTOK = 3.0
_CLAUDE_OUTPUT_COST_PER_MTOK = 15.0

# ── Claude Haiku 3 pricing (USD) ──────────────────────────────
# _CLAUDE_INPUT_COST_PER_MTOK = 0.25
# _CLAUDE_OUTPUT_COST_PER_MTOK = 1.25


# ── Image model estimates ────────────────────────────────────────
_DALLE3_HD_COST = 0.080
_DALLE3_STD_COST = 0.040

# Gemini / Imagen approx
_GEMINI_IMAGE_COST = 0.067   # ~1024px image


def estimate_dalle_cost(quality: str = "hd") -> float:
    return _DALLE3_HD_COST if quality == "hd" else _DALLE3_STD_COST


def estimate_gemini_image_cost() -> float:
    return _GEMINI_IMAGE_COST


def estimate_claude_cost(input_tokens: int, output_tokens: int) -> float:
    return (
        (input_tokens / 1_000_000) * _CLAUDE_INPUT_COST_PER_MTOK
        + (output_tokens / 1_000_000) * _CLAUDE_OUTPUT_COST_PER_MTOK
    )


def estimate_panel_cost(
    image_model: ImageModel,
    quality: str,
    input_tokens: int = 1500,
    output_tokens: int = 300,
) -> float:

    image_cost = (
        estimate_dalle_cost(quality)
        if image_model == ImageModel.DALLE3
        else estimate_gemini_image_cost()
    )

    claude_cost = estimate_claude_cost(input_tokens, output_tokens)

    return image_cost + claude_cost


def estimate_project_cost(
    panel_count: int,
    image_model: ImageModel,
    quality: str = "hd",
) -> float:

    # arc detection call
    arc_cost = estimate_claude_cost(2000, 500)

    panel_cost = estimate_panel_cost(image_model, quality)

    return arc_cost + panel_count * panel_cost