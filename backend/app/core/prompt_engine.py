"""
Stage 4 — LLM Prompt Engineering via Claude.

Converts a plain text segment into a rich, visually descriptive
image generation prompt. Injects arc context, style profile,
and narrative continuity from prior panels.
"""
from __future__ import annotations

import json
from typing import List, Optional

import anthropic

from app.core.style_engine import StyleEngine
from app.models.enums import (
    ArcType,
    DominantEmotion,
    ImageModel,
    PanelRole,
    StyleProfile,
)
from app.models.project import ArcDetectionResult, TextSegment
from app.utils.errors import PromptEngineeringError
from app.utils.logger import get_logger

logger = get_logger(__name__)

_SYSTEM_PROMPT = """\
You are a world-class visual director and AI art prompt engineer.
Your task: transform a narrative text segment into a highly detailed,
visually evocative prompt for an AI image generation model.

STRICT RULES:
1. Output ONLY valid JSON. No markdown fences, no preamble, no explanation.
2. Never include readable text, words, signs, letters, or numbers in the scene.
3. Describe: subject, scene composition, lighting, colour mood, camera angle, atmosphere.
4. Adapt visual intensity to the panel's emotional weight (intensity field).
5. Maintain visual continuity with the previous panel (if provided).
6. Keep visual_prompt under 180 words.

OUTPUT JSON SCHEMA:
{
  "scene_title": "<2-5 word evocative title — no spoilers>",
  "visual_prompt": "<rich image generation prompt>",
  "mood": "<single mood word>",
  "key_elements": ["<element1>", "<element2>", "<element3>"]
}
"""

_INTENSITY_GUIDANCE = {
    "low":    "Soft, calm composition. Natural ambient light. Peaceful, establishing atmosphere.",
    "medium": "Balanced, engaging scene. Directional lighting. Clear focus on subject.",
    "high":   "Dramatic, high-contrast composition. Strong directional light or chiaroscuro. Dynamic angle. Maximum visual impact.",
}

_ROLE_VISUAL_HINTS = {
    PanelRole.SETUP:       "wide establishing shot, context-setting, peaceful or expectant mood",
    PanelRole.TENSION:     "tight framing, dramatic shadows, unsettled or conflicted atmosphere",
    PanelRole.CLIMAX:      "peak action or emotion, maximum impact, dynamic composition",
    PanelRole.RESOLUTION:  "open space, clarity, warmth, sense of arrival or relief",
    PanelRole.CTA:         "forward motion, bright energy, aspirational and action-oriented",
    PanelRole.CONTEXT:     "clean, informational composition, documentary-style clarity",
}


def _intensity_label(intensity: float) -> str:
    if intensity < 0.4:
        return "low"
    if intensity < 0.7:
        return "medium"
    return "high"


def _build_user_message(
    segment: TextSegment,
    arc_result: ArcDetectionResult,
    style_profile: StyleProfile,
    style_suffix: str,
    prev_title: Optional[str],
    total_panels: int,
) -> str:
    panel_meta = arc_result.panels[segment.index]
    intensity_label = _intensity_label(panel_meta.intensity)
    role_hint = _ROLE_VISUAL_HINTS.get(panel_meta.role, "")

    parts = [
        f"STYLE PROFILE: {style_profile.value}",
        f"STYLE VISUAL DNA (append to prompt): {style_suffix}",
        "",
        f"NARRATIVE CONTEXT:",
        f"  Overall story arc: {arc_result.overall_arc.value}",
        f"  This panel's narrative role: {panel_meta.role.value} — {role_hint}",
        f"  Emotional intensity: {panel_meta.intensity}/1.0 ({intensity_label})",
        f"  Intensity guidance: {_INTENSITY_GUIDANCE[intensity_label]}",
        f"  Dominant emotion: {panel_meta.dominant_emotion.value}",
        f"  Panel {segment.index + 1} of {total_panels}",
    ]

    if prev_title:
        parts.append(f"  Previous panel title: '{prev_title}' (maintain visual continuity)")

    parts += [
        "",
        f"TEXT SEGMENT TO VISUALISE:",
        f'"{segment.text}"',
        "",
        "Generate the visual prompt JSON for this panel.",
    ]

    return "\n".join(parts)


def _parse_prompt_response(raw: str) -> dict:
    """Extract JSON from Claude response, handling minor formatting issues."""
    raw = raw.strip()
    # Strip markdown fences if Claude added them despite instructions
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1]) if len(lines) > 2 else raw
    return json.loads(raw)


class PromptEngineeringService:
    """Generates rich visual prompts for each storyboard panel using Claude."""

    def __init__(self, api_key: str, model: str) -> None:
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._style_engine = StyleEngine()

    async def engineer_prompt(
        self,
        segment: TextSegment,
        arc_result: ArcDetectionResult,
        style_profile: StyleProfile,
        prev_title: Optional[str] = None,
        total_panels: int = 1,
    ) -> dict:
        """
        Returns a dict with keys:
          scene_title, visual_prompt, mood, key_elements
        """
        style_config = self._style_engine.get_config(style_profile)
        user_msg = _build_user_message(
            segment=segment,
            arc_result=arc_result,
            style_profile=style_profile,
            style_suffix=style_config.suffix,
            prev_title=prev_title,
            total_panels=total_panels,
        )

        logger.info(
            "Engineering prompt",
            panel_index=segment.index,
            role=arc_result.panels[segment.index].role.value,
            intensity=arc_result.panels[segment.index].intensity,
        )

        try:
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._client.messages.create(
                    model=self._model,
                    max_tokens=600,
                    system=_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_msg}],
                ),
            )

            raw = response.content[0].text
            data = _parse_prompt_response(raw)

            # Apply style suffix to the visual_prompt
            visual_prompt_with_style = self._style_engine.apply_style(
                data.get("visual_prompt", segment.text), style_profile
            )

            prompt_tokens = response.usage.input_tokens + response.usage.output_tokens

            return {
                "scene_title": data.get("scene_title", f"Panel {segment.index + 1}"),
                "visual_prompt": visual_prompt_with_style,
                "engineered_prompt": data.get("visual_prompt", segment.text),
                "mood": data.get("mood", "neutral"),
                "key_elements": data.get("key_elements", []),
                "prompt_tokens": prompt_tokens,
            }

        except (json.JSONDecodeError, KeyError) as exc:
            logger.warning(
                "Prompt parse failed, using fallback",
                panel_index=segment.index,
                error=str(exc),
            )
            return self._fallback_prompt(segment, style_profile)

        except anthropic.APIStatusError as exc:
            raise PromptEngineeringError(
                f"Claude API error on panel {segment.index}: {exc.message}",
                detail={"panel_index": segment.index, "status_code": exc.status_code},
            ) from exc

    def _fallback_prompt(self, segment: TextSegment, style_profile: StyleProfile) -> dict:
        """Minimal fallback when Claude fails. Ensures generation can continue."""
        style_config = self._style_engine.get_config(style_profile)
        base = f"A visual scene depicting: {segment.text[:200]}"
        return {
            "scene_title": f"Scene {segment.index + 1}",
            "visual_prompt": f"{base}. {style_config.suffix}",
            "engineered_prompt": base,
            "mood": "neutral",
            "key_elements": [],
            "prompt_tokens": 0,
        }

    async def preview_prompt(
        self,
        text: str,
        style_profile: StyleProfile,
        panel_role: PanelRole,
        intensity: float,
        dominant_emotion: DominantEmotion,
    ) -> dict:
        """
        Generate a prompt preview without calling the image API.
        Used by the frontend panel editor.
        """
        from app.models.enums import ArcType
        from app.models.project import ArcDetectionResult, ArcPanelMeta, TextSegment

        fake_segment = TextSegment(index=0, text=text, token_count=len(text.split()))
        fake_arc = ArcDetectionResult(
            overall_arc=ArcType.INSPIRATIONAL,
            panels=[ArcPanelMeta(
                index=0,
                role=panel_role,
                intensity=intensity,
                dominant_emotion=dominant_emotion,
            )],
        )
        return await self.engineer_prompt(
            segment=fake_segment,
            arc_result=fake_arc,
            style_profile=style_profile,
            total_panels=1,
        )