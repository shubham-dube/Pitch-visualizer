"""Unit tests for the arc detector."""
import json
import pytest

from app.core.arc_detector import _default_arc, _parse_arc_result
from app.models.enums import ArcType, DominantEmotion, PanelRole


class TestDefaultArc:
    def test_returns_correct_panel_count(self):
        result = _default_arc(5)
        assert len(result.panels) == 5

    def test_all_panels_have_valid_data(self):
        result = _default_arc(4)
        for p in result.panels:
            assert 0.0 <= p.intensity <= 1.0
            assert p.role in PanelRole
            assert p.dominant_emotion in DominantEmotion

    def test_indices_are_sequential(self):
        result = _default_arc(6)
        for i, p in enumerate(result.panels):
            assert p.index == i

    def test_overall_arc_is_set(self):
        result = _default_arc(3)
        assert result.overall_arc in ArcType


class TestParseArcResult:
    def test_parses_valid_json(self):
        raw = json.dumps({
            "overall_arc": "problem_solution",
            "panels": [
                {"index": 0, "role": "setup", "intensity": 0.2, "dominant_emotion": "calm"},
                {"index": 1, "role": "tension", "intensity": 0.7, "dominant_emotion": "tense"},
                {"index": 2, "role": "resolution", "intensity": 0.5, "dominant_emotion": "hopeful"},
            ]
        })
        result = _parse_arc_result(raw, segment_count=3)
        assert result.overall_arc == ArcType.PROBLEM_SOLUTION
        assert len(result.panels) == 3
        assert result.panels[0].role == PanelRole.SETUP
        assert result.panels[1].intensity == 0.7

    def test_falls_back_on_invalid_json(self):
        result = _parse_arc_result("not valid json at all", segment_count=3)
        assert len(result.panels) == 3
        assert result.overall_arc in ArcType

    def test_fills_missing_panels_with_defaults(self):
        raw = json.dumps({
            "overall_arc": "journey",
            "panels": [
                {"index": 0, "role": "setup", "intensity": 0.3, "dominant_emotion": "calm"},
                # panel 1 and 2 missing
            ]
        })
        result = _parse_arc_result(raw, segment_count=3)
        assert len(result.panels) == 3

    def test_clamps_intensity_to_valid_range(self):
        raw = json.dumps({
            "overall_arc": "inspirational",
            "panels": [
                {"index": 0, "role": "setup", "intensity": 5.0, "dominant_emotion": "calm"},
            ]
        })
        result = _parse_arc_result(raw, segment_count=1)
        assert result.panels[0].intensity <= 1.0

    def test_ignores_unknown_roles_gracefully(self):
        raw = json.dumps({
            "overall_arc": "inspirational",
            "panels": [
                {"index": 0, "role": "totally_unknown_role", "intensity": 0.5, "dominant_emotion": "calm"},
            ]
        })
        # Should fall back to default for that panel
        result = _parse_arc_result(raw, segment_count=1)
        assert len(result.panels) == 1