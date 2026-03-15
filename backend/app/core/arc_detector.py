"""
Stage 2 — Narrative Arc Detection (Innovation Layer).

Sends the full set of segments to Claude and receives:
  - overall_arc type (problem_solution, journey, etc.)
  - per-panel: role, intensity score, dominant emotion

This enriches every subsequent stage with story context.
"""
from __future__ import annotations

import json
from typing import List

import anthropic

from app.models.enums import ArcType, DominantEmotion, PanelRole
from app.models.project import ArcDetectionResult, ArcPanelMeta, TextSegment
from app.utils.errors import ArcDetectionError
from app.utils.logger import get_logger

logger = get_logger(__name__)

_SYSTEM_PROMPT = """\
You are a narrative analyst specialising in visual storytelling.
Analyse the provided story segments and classify them into a narrative structure.

OUTPUT: Return ONLY a valid JSON object. No markdown, no commentary, no code fences.

JSON SCHEMA:
{
  "overall_arc": <one of: "problem_solution" | "journey" | "transformation" | "comparison" | "timeline" | "inspirational">,
  "panels": [
    {
      "index": <int>,
      "role": <one of: "setup" | "tension" | "climax" | "resolution" | "cta" | "context">,
      "intensity": <float 0.0-1.0, where 0=calm/neutral, 1=maximum drama/urgency>,
      "dominant_emotion": <one of: "hopeful" | "tense" | "triumphant" | "urgent" | "calm" | "inspiring" | "concerned" | "excited" | "neutral">
    }
  ]
}

ROLE GUIDE:
- setup: introduces the situation, characters, or context
- tension: presents a problem, conflict, or challenge
- climax: the peak moment, turning point, or key insight
- resolution: the outcome, solution, or answer
- cta: call to action, next step, or forward momentum
- context: factual or background information

INTENSITY GUIDE:
- 0.0-0.3: calm, informational, establishing
- 0.4-0.6: moderate, building, meaningful
- 0.7-1.0: high stakes, dramatic, triumphant, urgent
"""


def _build_user_message(segments: List[TextSegment]) -> str:
    segments_json = json.dumps(
        [{"index": s.index, "text": s.text} for s in segments],
        indent=2,
    )
    return f"STORY SEGMENTS:\n{segments_json}\n\nAnalyse these segments and return the arc JSON."


def _parse_arc_result(raw: str, segment_count: int) -> ArcDetectionResult:
    """Parse and validate Claude's JSON response. Falls back to defaults on any error."""
    try:
        data = json.loads(raw.strip())
        overall_arc = ArcType(data.get("overall_arc", "inspirational"))

        panels_raw = data.get("panels", [])
        panels: List[ArcPanelMeta] = []

        for p in panels_raw:
            try:
                panel = ArcPanelMeta(
                    index=int(p["index"]),
                    role=PanelRole(p.get("role", "context")),
                    intensity=float(max(0.0, min(1.0, p.get("intensity", 0.5)))),
                    dominant_emotion=DominantEmotion(p.get("dominant_emotion", "neutral")),
                )
                panels.append(panel)
            except (KeyError, ValueError) as e:
                logger.warning("Skipping malformed arc panel", error=str(e), raw_panel=p)

        # Ensure all segments have arc data (fill missing with defaults)
        indexed = {p.index: p for p in panels}
        full_panels = []
        for i in range(segment_count):
            if i in indexed:
                full_panels.append(indexed[i])
            else:
                full_panels.append(ArcPanelMeta(
                    index=i,
                    role=PanelRole.CONTEXT,
                    intensity=0.5,
                    dominant_emotion=DominantEmotion.NEUTRAL,
                ))

        return ArcDetectionResult(overall_arc=overall_arc, panels=full_panels)

    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Arc detection parse failed, using defaults", error=str(exc))
        return _default_arc(segment_count)


def _default_arc(segment_count: int) -> ArcDetectionResult:
    """Graceful fallback: linear arc with escalating intensity."""
    roles = [PanelRole.SETUP, PanelRole.TENSION, PanelRole.CLIMAX,
             PanelRole.RESOLUTION, PanelRole.CTA]
    panels = []
    for i in range(segment_count):
        role = roles[min(i, len(roles) - 1)]
        intensity = min(0.3 + i * 0.15, 1.0)
        panels.append(ArcPanelMeta(
            index=i,
            role=role,
            intensity=round(intensity, 2),
            dominant_emotion=DominantEmotion.NEUTRAL,
        ))
    return ArcDetectionResult(overall_arc=ArcType.INSPIRATIONAL, panels=panels)


class ArcDetectionService:
    """Detects the narrative arc of the full storyboard using Claude."""

    def __init__(self, api_key: str, model: str) -> None:
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    async def detect(
        self, segments: List[TextSegment]
    ) -> ArcDetectionResult:
        if not segments:
            raise ArcDetectionError("Cannot detect arc: no segments provided.")

        logger.info("Running arc detection", segment_count=len(segments), model=self._model)

        try:
            # Claude client is sync; run in executor to avoid blocking event loop
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._client.messages.create(
                    model=self._model,
                    max_tokens=800,
                    system=_SYSTEM_PROMPT,
                    messages=[
                        {"role": "user", "content": _build_user_message(segments)}
                    ],
                ),
            )

            raw_text = response.content[0].text
            result = _parse_arc_result(raw_text, len(segments))
            logger.info("Arc detection complete", overall_arc=result.overall_arc)
            return result

        except anthropic.APIStatusError as exc:
            logger.error("Anthropic API error in arc detection", status=exc.status_code, error=str(exc))
            logger.warning("Falling back to default arc")
            return _default_arc(len(segments))

        except Exception as exc:
            logger.error("Unexpected error in arc detection", error=str(exc))
            return _default_arc(len(segments))