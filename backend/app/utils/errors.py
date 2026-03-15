"""
Custom exception hierarchy for the application.
All pipeline errors inherit from PitchVisualizerError for uniform handling.
"""
from __future__ import annotations


class PitchVisualizerError(Exception):
    """Base exception for all application errors."""
    code: str = "INTERNAL_ERROR"
    http_status: int = 500

    def __init__(self, message: str, detail: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail or {}


class ProjectNotFoundError(PitchVisualizerError):
    code = "PROJECT_NOT_FOUND"
    http_status = 404


class ValidationError(PitchVisualizerError):
    code = "VALIDATION_ERROR"
    http_status = 422


class SegmentationError(PitchVisualizerError):
    code = "SEGMENTATION_FAILED"
    http_status = 500


class ArcDetectionError(PitchVisualizerError):
    code = "ARC_DETECTION_FAILED"
    http_status = 500


class PromptEngineeringError(PitchVisualizerError):
    code = "PROMPT_ENGINEERING_FAILED"
    http_status = 500


class ImageGenerationError(PitchVisualizerError):
    code = "IMAGE_GENERATION_FAILED"
    http_status = 502


class ContentPolicyError(ImageGenerationError):
    code = "CONTENT_POLICY_VIOLATION"
    http_status = 422


class RateLimitError(PitchVisualizerError):
    code = "RATE_LIMIT_EXCEEDED"
    http_status = 429


class StorageError(PitchVisualizerError):
    code = "STORAGE_ERROR"
    http_status = 500


class ExternalAPIError(PitchVisualizerError):
    code = "EXTERNAL_API_ERROR"
    http_status = 502