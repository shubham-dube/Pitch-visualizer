"""
Stage 1 — Intelligent Text Segmentation.

Uses spaCy for sentence boundary detection, then applies:
  - Merge logic for very short sentences
  - TF-IDF clustering for long texts (> max_panels sentences)
  - Guaranteed min/max panel count
"""
from __future__ import annotations

import re
from typing import List

from app.models.project import TextSegment
from app.utils.errors import SegmentationError
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Lazy-loaded spaCy model
_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer"])
        except OSError:
            logger.warning("spaCy model not found; falling back to regex splitter")
            _nlp = "fallback"
    return _nlp


def _regex_split(text: str) -> List[str]:
    """Simple regex-based sentence splitter as spaCy fallback."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _spacy_split(text: str) -> List[str]:
    nlp = _get_nlp()
    if nlp == "fallback":
        return _regex_split(text)
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]


def _merge_short_sentences(sentences: List[str], min_tokens: int = 8) -> List[str]:
    """
    Merge sentences shorter than min_tokens with the previous or next sentence.
    This prevents tiny segments that produce weak visual prompts.
    """
    if not sentences:
        return sentences

    merged: List[str] = []
    buffer = ""

    for sent in sentences:
        word_count = len(sent.split())
        if buffer:
            combined = f"{buffer} {sent}"
            if word_count < min_tokens:
                # Still short, keep accumulating
                buffer = combined
            else:
                merged.append(combined.strip())
                buffer = ""
        else:
            if word_count < min_tokens:
                buffer = sent
            else:
                merged.append(sent)

    if buffer:
        # Flush remaining into last segment
        if merged:
            merged[-1] = f"{merged[-1]} {buffer}".strip()
        else:
            merged.append(buffer.strip())

    return merged


def _cluster_segments(sentences: List[str], target: int) -> List[str]:
    """
    Reduce a list of sentences to `target` clusters using TF-IDF + greedy merging.
    Falls back to equal-partition if sklearn is unavailable.
    """
    if len(sentences) <= target:
        return sentences

    try:
        import numpy as np
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vectorizer = TfidfVectorizer(stop_words="english", max_features=500)
        tfidf = vectorizer.fit_transform(sentences)
        sim_matrix = cosine_similarity(tfidf)

        # Greedy: repeatedly merge the most similar adjacent pair
        current = list(sentences)
        while len(current) > target:
            best_score = -1.0
            best_i = 0
            for i in range(len(current) - 1):
                v1 = vectorizer.transform([current[i]])
                v2 = vectorizer.transform([current[i + 1]])
                score = float(cosine_similarity(v1, v2)[0, 0])
                if score > best_score:
                    best_score = score
                    best_i = i
            merged_sent = f"{current[best_i]} {current[best_i + 1]}"
            current = current[:best_i] + [merged_sent] + current[best_i + 2 :]

        return current

    except Exception as exc:
        logger.warning("TF-IDF clustering failed, using equal partition", error=str(exc))
        # Fallback: equal-size partitions
        chunk_size = max(1, len(sentences) // target)
        chunks = []
        for i in range(0, len(sentences), chunk_size):
            chunk = " ".join(sentences[i : i + chunk_size])
            chunks.append(chunk)
        return chunks[:target]


class SegmentationService:
    """
    Converts raw narrative text into a list of TextSegment objects.
    Each segment maps to one storyboard panel.
    """

    def __init__(self, min_panels: int = 3, max_panels: int = 8) -> None:
        self.min_panels = min_panels
        self.max_panels = max_panels

    def segment(self, text: str, desired_panels: int = 5) -> List[TextSegment]:
        desired_panels = max(self.min_panels, min(desired_panels, self.max_panels))

        logger.info("Starting segmentation", text_length=len(text), desired_panels=desired_panels)

        try:
            raw_sentences = _spacy_split(text)
        except Exception as exc:
            raise SegmentationError(f"Failed to tokenize text: {exc}") from exc

        if not raw_sentences:
            raise SegmentationError("No sentences could be extracted from input text.")

        # Merge very short sentences
        sentences = _merge_short_sentences(raw_sentences, min_tokens=8)

        # Cluster if too many
        if len(sentences) > desired_panels:
            sentences = _cluster_segments(sentences, target=desired_panels)

        # Pad if too few (shouldn't happen in practice but be safe)
        while len(sentences) < self.min_panels and len(sentences) < desired_panels:
            # Split the longest sentence
            longest_i = max(range(len(sentences)), key=lambda i: len(sentences[i]))
            words = sentences[longest_i].split()
            mid = len(words) // 2
            left = " ".join(words[:mid])
            right = " ".join(words[mid:])
            sentences = sentences[:longest_i] + [left, right] + sentences[longest_i + 1 :]

        segments = [
            TextSegment(
                index=i,
                text=sent.strip(),
                token_count=len(sent.split()),
                is_merged=(len(_spacy_split(sent)) > 1 if _get_nlp() != "fallback" else False),
            )
            for i, sent in enumerate(sentences)
        ]

        logger.info(
            "Segmentation complete",
            input_sentences=len(raw_sentences),
            output_segments=len(segments),
        )
        return segments