"""
Shared enumerations used across models and API schemas.
"""
from enum import Enum


class ProjectStatus(str, Enum):
    QUEUED = "queued"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class PanelStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    DONE = "done"
    FAILED = "failed"


class ImageModel(str, Enum):
    DALLE3 = "dalle3"
    GEMINI = "gemini"


class StyleProfile(str, Enum):
    CORPORATE = "corporate"
    CINEMATIC = "cinematic"
    STORYBOOK = "storybook"
    MINIMAL = "minimal"
    FUTURISTIC = "futuristic"
    DOCUMENTARY = "documentary"


class PanelRole(str, Enum):
    SETUP = "setup"
    TENSION = "tension"
    CLIMAX = "climax"
    RESOLUTION = "resolution"
    CTA = "cta"
    CONTEXT = "context"


class ArcType(str, Enum):
    PROBLEM_SOLUTION = "problem_solution"
    JOURNEY = "journey"
    TRANSFORMATION = "transformation"
    COMPARISON = "comparison"
    TIMELINE = "timeline"
    INSPIRATIONAL = "inspirational"


class DominantEmotion(str, Enum):
    HOPEFUL = "hopeful"
    TENSE = "tense"
    TRIUMPHANT = "triumphant"
    URGENT = "urgent"
    CALM = "calm"
    INSPIRING = "inspiring"
    CONCERNED = "concerned"
    EXCITED = "excited"
    NEUTRAL = "neutral"


class GenerationStage(str, Enum):
    SEGMENTING = "segmenting"
    ARC_DETECTION = "arc_detection"
    PROMPT_ENGINEERING = "prompt_engineering"
    IMAGE_GENERATION = "image_generation"
    ASSEMBLING = "assembling"
    DONE = "done"