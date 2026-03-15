"""
Style Engine — maps style profiles to visual DNA suffixes.
Also determines the DALL-E "style" param (vivid vs natural)
and Gemini style hints.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from app.models.enums import StyleProfile


@dataclass(frozen=True)
class StyleConfig:
    display_name: str
    description: str
    visual_vibe: str
    best_for: str
    suffix: str                  # Appended to every visual prompt
    dalle_style: str             # "vivid" | "natural"
    gemini_style_hint: str       # Appended for Gemini
    mood_color_map: Dict[str, list]  # emotion → suggested hex palette


_STYLES: Dict[StyleProfile, StyleConfig] = {
    StyleProfile.CORPORATE: StyleConfig(
        display_name="Corporate / Professional",
        description="Clean, polished, trust-inspiring visuals",
        visual_vibe="Boardrooms, handshakes, clean data",
        best_for="B2B pitches, investor decks, case studies",
        suffix=(
            "professional corporate photography, "
            "soft diffused studio lighting, clean neutral background, "
            "executive aesthetic, sharp focus, 4K photorealistic, "
            "Canon EOS R5 quality"
        ),
        dalle_style="natural",
        gemini_style_hint="photorealistic professional photography style",
        mood_color_map={
            "hopeful":    ["#1E3A5F", "#FFFFFF", "#2196F3"],
            "triumphant": ["#0D47A1", "#FFD700", "#FFFFFF"],
            "calm":       ["#37474F", "#ECEFF1", "#78909C"],
            "inspiring":  ["#1565C0", "#E3F2FD", "#42A5F5"],
            "neutral":    ["#455A64", "#F5F5F5", "#90A4AE"],
        },
    ),
    StyleProfile.CINEMATIC: StyleConfig(
        display_name="Cinematic / Film",
        description="Dramatic, film-quality, emotionally rich",
        visual_vibe="Golden hour, lens flares, epic depth of field",
        best_for="Brand stories, product launches, emotional narratives",
        suffix=(
            "cinematic widescreen film still, anamorphic lens, "
            "Kodak Vision3 color grading, dramatic depth of field, "
            "directional key light, 2.39:1 aspect ratio, "
            "award-winning cinematography, IMAX quality"
        ),
        dalle_style="vivid",
        gemini_style_hint="cinematic film photography style with dramatic lighting",
        mood_color_map={
            "tense":      ["#1A1A2E", "#E94560", "#16213E"],
            "triumphant": ["#F5A623", "#1A1A2E", "#FF6B35"],
            "hopeful":    ["#F8B500", "#2C3E50", "#E8D5B7"],
            "concerned":  ["#2D3436", "#636E72", "#B2BEC3"],
            "neutral":    ["#2C3E50", "#ECF0F1", "#95A5A6"],
        },
    ),
    StyleProfile.STORYBOOK: StyleConfig(
        display_name="Storybook / Illustrated",
        description="Warm, hand-crafted, whimsical watercolour",
        visual_vibe="Watercolour textures, warm palettes, fantasy feel",
        best_for="Consumer brands, education, healthcare, children",
        suffix=(
            "hand-painted children's book illustration, warm watercolour texture, "
            "soft pastel gradient palette, loose detailed brushwork, "
            "golden ratio composition, warm ambient light, "
            "Beatrix Potter meets modern editorial"
        ),
        dalle_style="vivid",
        gemini_style_hint="watercolor illustration style, warm and whimsical",
        mood_color_map={
            "hopeful":    ["#FFD166", "#EF476F", "#06D6A0"],
            "calm":       ["#AED9E0", "#FAF3DD", "#B8F2E6"],
            "inspiring":  ["#FFBE0B", "#FB5607", "#3A86FF"],
            "neutral":    ["#E9C46A", "#F4A261", "#E76F51"],
        },
    ),
    StyleProfile.MINIMAL: StyleConfig(
        display_name="Minimal / Modern",
        description="Ultra-clean, geometric, Swiss design school",
        visual_vibe="Negative space, flat geometry, 2-tone palette",
        best_for="SaaS, fintech, design tools, startup pitches",
        suffix=(
            "ultra-minimalist flat design, geometric abstract forms, "
            "vast negative white space, 2-colour palette only, "
            "Swiss International Typographic Style, Bauhaus influence, "
            "clean editorial, vector-like precision"
        ),
        dalle_style="natural",
        gemini_style_hint="minimalist flat design illustration, geometric, clean",
        mood_color_map={
            "neutral":    ["#000000", "#FFFFFF", "#F5F5F5"],
            "inspiring":  ["#FF3B30", "#FFFFFF", "#000000"],
            "calm":       ["#007AFF", "#FFFFFF", "#F2F2F7"],
            "excited":    ["#FF9500", "#000000", "#FFFFFF"],
        },
    ),
    StyleProfile.FUTURISTIC: StyleConfig(
        display_name="Futuristic / Tech",
        description="Dark, neon-lit, Blade Runner aesthetic",
        visual_vibe="Holographics, neon accents, tech interfaces",
        best_for="AI/ML products, cybersecurity, tech vision pitches",
        suffix=(
            "sci-fi concept art, dark atmospheric night scene, "
            "electric neon accent lighting, holographic data elements, "
            "Blade Runner 2049 aesthetic, ultra-detailed, "
            "cinematic dark background, volumetric light rays"
        ),
        dalle_style="vivid",
        gemini_style_hint="futuristic sci-fi digital art, neon cyberpunk aesthetic",
        mood_color_map={
            "tense":      ["#0D0D0D", "#FF2079", "#1A1A2E"],
            "excited":    ["#00FFF0", "#FF00FF", "#0D0D0D"],
            "inspiring":  ["#00D4FF", "#0D0D0D", "#7B2FBE"],
            "neutral":    ["#1A1A2E", "#16213E", "#0F3460"],
        },
    ),
    StyleProfile.DOCUMENTARY: StyleConfig(
        display_name="Documentary / Real",
        description="Authentic, photojournalistic, candid",
        visual_vibe="Natural light, real people, raw moments",
        best_for="Social impact, NGO, authentic brand stories",
        suffix=(
            "editorial documentary photography, natural ambient light, "
            "authentic candid moment, photojournalism style, "
            "Leica street photography, subtle film grain, "
            "honest human emotion, golden hour natural tones"
        ),
        dalle_style="natural",
        gemini_style_hint="documentary photography style, natural light, candid",
        mood_color_map={
            "concerned":  ["#5D4037", "#BCAAA4", "#3E2723"],
            "hopeful":    ["#E65100", "#FFF8E1", "#FF8F00"],
            "calm":       ["#33691E", "#F9FBE7", "#558B2F"],
            "neutral":    ["#616161", "#FAFAFA", "#9E9E9E"],
        },
    ),
}


class StyleEngine:
    """Applies style profiles to visual prompts and provides config info."""

    def get_config(self, profile: StyleProfile) -> StyleConfig:
        return _STYLES[profile]

    def apply_style(self, visual_prompt: str, profile: StyleProfile) -> str:
        """Append the style suffix to a visual prompt."""
        config = _STYLES[profile]
        return f"{visual_prompt.rstrip('.')}. {config.suffix}"

    def get_color_palette(
        self, profile: StyleProfile, emotion: str
    ) -> list:
        """Return a suggested hex palette for the given profile + emotion."""
        config = _STYLES[profile]
        palette = config.mood_color_map.get(emotion)
        if not palette:
            # Return first available palette as default
            palette = next(iter(config.mood_color_map.values()))
        return palette

    def get_dalle_style(self, profile: StyleProfile) -> str:
        return _STYLES[profile].dalle_style

    def all_profiles(self) -> Dict[StyleProfile, StyleConfig]:
        return _STYLES