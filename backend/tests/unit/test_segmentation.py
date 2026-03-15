"""Unit tests for the segmentation service."""
import pytest
from unittest.mock import patch, MagicMock

from app.core.segmentation import SegmentationService, _merge_short_sentences, _cluster_segments
from app.utils.errors import SegmentationError


class TestMergeShortSentences:
    def test_merges_short_sentence_with_next(self):
        result = _merge_short_sentences(["Hi.", "This is a longer sentence with enough tokens."], min_tokens=5)
        assert len(result) == 1
        assert "Hi." in result[0]

    def test_keeps_long_sentences_separate(self):
        sentences = [
            "This is a sufficiently long sentence for testing.",
            "And this is another sufficiently long sentence here.",
        ]
        result = _merge_short_sentences(sentences, min_tokens=5)
        assert len(result) == 2

    def test_handles_empty_input(self):
        assert _merge_short_sentences([]) == []

    def test_flushes_trailing_buffer(self):
        result = _merge_short_sentences(
            ["Long enough sentence to pass the test here.", "Short."],
            min_tokens=5,
        )
        assert len(result) == 1
        assert "Short." in result[0]


class TestClusterSegments:
    def test_returns_same_if_already_within_target(self):
        sentences = ["Sentence one.", "Sentence two.", "Sentence three."]
        result = _cluster_segments(sentences, target=5)
        assert result == sentences

    def test_reduces_to_target(self):
        sentences = [f"This is sentence number {i} in the list." for i in range(8)]
        result = _cluster_segments(sentences, target=4)
        assert len(result) == 4

    def test_handles_single_sentence(self):
        result = _cluster_segments(["Only one sentence."], target=3)
        assert len(result) == 1


class TestSegmentationService:
    def setup_method(self):
        self.service = SegmentationService(min_panels=3, max_panels=8)

    @patch("app.core.segmentation._get_nlp")
    def test_basic_segmentation(self, mock_nlp):
        mock_nlp.return_value = "fallback"
        text = "First sentence. Second sentence here. Third sentence is here. Fourth sentence too."
        result = self.service.segment(text, desired_panels=4)
        assert len(result) >= 3
        for seg in result:
            assert seg.text
            assert seg.index >= 0

    @patch("app.core.segmentation._get_nlp")
    def test_respects_min_panels(self, mock_nlp):
        mock_nlp.return_value = "fallback"
        text = "Only one sentence."
        result = self.service.segment(text, desired_panels=3)
        assert len(result) >= self.service.min_panels

    @patch("app.core.segmentation._get_nlp")
    def test_respects_max_panels(self, mock_nlp):
        mock_nlp.return_value = "fallback"
        # Very long text
        text = " ".join([f"This is sentence number {i} in a very long document." for i in range(20)])
        result = self.service.segment(text, desired_panels=8)
        assert len(result) <= self.service.max_panels

    @patch("app.core.segmentation._get_nlp")
    def test_segment_indices_are_sequential(self, mock_nlp):
        mock_nlp.return_value = "fallback"
        text = "First. Second third fourth fifth. More words here please. And even more words."
        result = self.service.segment(text, desired_panels=3)
        for i, seg in enumerate(result):
            assert seg.index == i

    @patch("app.core.segmentation._get_nlp")
    def test_raises_on_empty_text(self, mock_nlp):
        mock_nlp.return_value = "fallback"
        with pytest.raises(SegmentationError):
            self.service.segment("   ", desired_panels=3)