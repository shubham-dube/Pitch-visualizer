"""
Cost estimation utilities.
Keeps rough running estimates so users can see approximate spend.
"""
from __future__ import annotations

from app.models.enums import ImageModel


# ── Approximate pricing (USD) as of late 2024 ────────────────────
_CLAUDE_INPUT_COST_PER_1K  = 0.003    # claude-opus-4-5
_CLAUDE_OUTPUT_COST_PER_1K = 0.015

_DALLE3_HD_COST     = 0.080   # per image, 1792×1024
_DALLE3_STD_COST    = 0.040

_GEMINI_IMAGE_COST  = 0.040   # Imagen 3 per image (approximate)


def estimate_dalle_cost(quality: str = "hd") -> float:
    return _DALLE3_HD_COST if quality == "hd" else _DALLE3_STD_COST


def estimate_gemini_image_cost() -> float:
    return _GEMINI_IMAGE_COST


def estimate_claude_cost(input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens / 1000 * _CLAUDE_INPUT_COST_PER_1K
        + output_tokens / 1000 * _CLAUDE_OUTPUT_COST_PER_1K
    )


def estimate_panel_cost(image_model: ImageModel, quality: str = "hd") -> float:
    image_cost = (
        estimate_dalle_cost(quality)
        if image_model == ImageModel.DALLE3
        else estimate_gemini_image_cost()
    )
    # Add ~$0.01 for Claude prompt engineering per panel
    return image_cost + 0.01


def estimate_project_cost(
    panel_count: int, image_model: ImageModel, quality: str = "hd"
) -> float:
    # Arc detection: ~$0.03 flat
    arc_cost = 0.03
    return arc_cost + panel_count * estimate_panel_cost(image_model, quality)