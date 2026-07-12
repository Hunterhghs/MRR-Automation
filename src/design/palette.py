"""Algorithmic color palette generation using color-theory harmony rules.

Produces perceptually coherent palettes from a seed value.
Each palette contains: primary, secondary, accent, neutral (light + dark),
plus semantic colors for charts and callouts.
"""

import colorsys
import random
from dataclasses import dataclass, field


@dataclass
class Palette:
    """A generated color palette for a report."""
    name: str
    primary: str         # Dominant brand color (headings, cover bg)
    secondary: str       # Supporting color (subheadings, rules)
    accent: str          # Pop color (callouts, highlights)
    neutral_dark: str    # Body text, dark backgrounds
    neutral_light: str   # Page background, light fills
    neutral_mid: str     # Borders, subtle rules
    chart_colors: list[str] = field(default_factory=list)  # 5+ data colors
    semantic: dict[str, str] = field(default_factory=dict)  # positive, negative, warning

    @property
    def hex_primary(self) -> tuple:
        return _hex_to_rgb(self.primary)

    @property
    def hex_secondary(self) -> tuple:
        return _hex_to_rgb(self.secondary)

    @property
    def hex_accent(self) -> tuple:
        return _hex_to_rgb(self.accent)

    @property
    def hex_dark(self) -> tuple:
        return _hex_to_rgb(self.neutral_dark)

    @property
    def hex_light(self) -> tuple:
        return _hex_to_rgb(self.neutral_light)

    @property
    def hex_mid(self) -> tuple:
        return _hex_to_rgb(self.neutral_mid)


# ── Utility functions ──────────────────────────────────────────────────

def _hsl_to_hex(h: float, s: float, l: float) -> str:
    """Convert HSL (0–1 ranges) to hex string."""
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def _hex_to_rgb(hex_str: str) -> tuple:
    """Convert hex string to (r, g, b) 0–255 tuple."""
    hex_str = hex_str.lstrip("#")
    return (
        int(hex_str[0:2], 16),
        int(hex_str[2:4], 16),
        int(hex_str[4:6], 16),
    )


def _hex_to_hsl(hex_str: str) -> tuple:
    """Convert hex string to HSL (0–1 ranges)."""
    r, g, b = _hex_to_rgb(hex_str)
    return colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)


def hex_to_rgb_normalized(hex_str: str) -> tuple:
    """Convert hex string to (r, g, b) 0.0–1.0 tuple."""
    r, g, b = _hex_to_rgb(hex_str)
    return (r / 255.0, g / 255.0, b / 255.0)


def _seed_random(seed: int) -> random.Random:
    """Create a deterministic Random from an integer seed."""
    return random.Random(seed)


# ── Harmony rules ──────────────────────────────────────────────────────

HARMONY_RULES = [
    "complementary",
    "split_complementary",
    "triadic",
    "analogous",
    "monochromatic",
]


def generate_palette(seed: int, name: str = "Generated") -> Palette:
    """Generate a full palette from a seed using a harmony rule.

    Args:
        seed: Integer seed for reproducibility.
        name: Label for the palette.

    Returns:
        A Palette with all colors filled in.
    """
    rng = _seed_random(seed)

    rule_idx = seed % len(HARMONY_RULES)
    rule = HARMONY_RULES[rule_idx]

    base_hue = (seed * 137.508) % 360

    if rule == "complementary":
        hues = _complementary(base_hue, rng)
    elif rule == "split_complementary":
        hues = _split_complementary(base_hue, rng)
    elif rule == "triadic":
        hues = _triadic(base_hue, rng)
    elif rule == "analogous":
        hues = _analogous(base_hue, rng)
    else:
        hues = _monochromatic(base_hue, rng)

    primary_h, secondary_h, accent_h = hues

    sat_primary = 0.45 + rng.random() * 0.35
    sat_secondary = 0.35 + rng.random() * 0.35
    sat_accent = 0.55 + rng.random() * 0.40

    light_primary = 0.28 + rng.random() * 0.18
    light_secondary = 0.40 + rng.random() * 0.20
    light_accent = 0.35 + rng.random() * 0.25

    primary = _hsl_to_hex(primary_h / 360, sat_primary, light_primary)
    secondary = _hsl_to_hex(secondary_h / 360, sat_secondary, light_secondary)
    accent = _hsl_to_hex(accent_h / 360, sat_accent, light_accent)

    is_warm = 0 <= primary_h <= 60 or 300 <= primary_h <= 360
    if is_warm:
        neutral_dark = _hsl_to_hex(primary_h / 360, 0.06, 0.12 + rng.random() * 0.06)
        neutral_light = _hsl_to_hex(primary_h / 360, 0.08, 0.93 + rng.random() * 0.04)
        neutral_mid = _hsl_to_hex(primary_h / 360, 0.10, 0.65 + rng.random() * 0.15)
    else:
        neutral_dark = _hsl_to_hex(primary_h / 360, 0.04, 0.10 + rng.random() * 0.08)
        neutral_light = _hsl_to_hex(primary_h / 360, 0.05, 0.93 + rng.random() * 0.04)
        neutral_mid = _hsl_to_hex(primary_h / 360, 0.08, 0.60 + rng.random() * 0.15)

    chart_hues = [(primary_h + i * 360 / 5) % 360 for i in range(5)]
    chart_colors = [
        _hsl_to_hex(h / 360, 0.50 + rng.random() * 0.30, 0.40 + rng.random() * 0.20)
        for h in chart_hues
    ]

    semantic = {
        "positive": _hsl_to_hex(150 / 360, 0.45, 0.35),
        "negative": _hsl_to_hex(0 / 360, 0.60, 0.42),
        "warning": _hsl_to_hex(45 / 360, 0.70, 0.48),
    }

    return Palette(
        name=name,
        primary=primary,
        secondary=secondary,
        accent=accent,
        neutral_dark=neutral_dark,
        neutral_light=neutral_light,
        neutral_mid=neutral_mid,
        chart_colors=chart_colors,
        semantic=semantic,
    )


def _complementary(base: float, rng: random.Random) -> tuple:
    primary = base
    secondary = (base + 180) % 360
    accent = (base + 90 + rng.random() * 60) % 360
    return primary, secondary, accent


def _split_complementary(base: float, rng: random.Random) -> tuple:
    primary = base
    offset = 150 + rng.random() * 60
    secondary = (base + offset) % 360
    accent = (base + offset + 180) % 360
    return primary, secondary, accent


def _triadic(base: float, rng: random.Random) -> tuple:
    primary = base
    secondary = (base + 120 + rng.random() * 20 - 10) % 360
    accent = (base + 240 + rng.random() * 20 - 10) % 360
    return primary, secondary, accent


def _analogous(base: float, rng: random.Random) -> tuple:
    primary = base
    secondary = (base + 25 + rng.random() * 15) % 360
    accent = (base + 50 + rng.random() * 20) % 360
    return primary, secondary, accent


def _monochromatic(base: float, rng: random.Random) -> tuple:
    primary = base
    secondary = base
    accent = (base + rng.random() * 30 - 15) % 360
    return primary, secondary, accent
