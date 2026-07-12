"""H Heuristics brand identity — fixed brand theme for all reports.

This overrides the algorithmic theme generation when the brand flag is set.
Colors match H Heuristics visual identity: professional, authoritative,
with a warm academic feel suitable for market research.

Each report gets a UNIQUE cover design via seed-based archetype selection
while maintaining the consistent H Heuristics color palette and typography.
"""

import random

from .palette import Palette
from .typography import Typography
from .theme import Theme, Layout, COVER_ARCHETYPES

# Brand-appropriate cover archetypes (professional, not experimental)
# Excludes: geometric (too playful for market research)
BRAND_COVER_ARCHETYPES = [
    "full_bleed",
    "split_horizontal",
    "framed",
    "minimal_center",
    "banded",
]

# H Heuristics Brand Palette
# Primary: Deep navy-blue — authority, trust, intelligence
# Secondary: Warm gold — insight, value, premium
# Accent: Teal — data, technology, precision
# Neutrals: Warm grey family

BRAND_PRIMARY = "#1a2744"      # Deep navy
BRAND_SECONDARY = "#c8923f"    # Warm gold
BRAND_ACCENT = "#2d8a7b"       # Teal
BRAND_DARK = "#1e293b"         # Slate-900
BRAND_LIGHT = "#f8fafc"        # Slate-50
BRAND_MID = "#64748b"          # Slate-500

BRAND_CHART_COLORS = [
    "#1a2744",  # Navy
    "#c8923f",  # Gold
    "#2d8a7b",  # Teal
    "#e8533f",  # Warm red
    "#3b82f6",  # Blue
    "#8b5cf6",  # Purple
    "#f59e0b",  # Amber
    "#10b981",  # Emerald
]

BRAND_SEMANTIC = {
    "positive": "#2d8a56",
    "negative": "#c0392b",
    "warning": "#d4a017",
}

BRAND_PALETTE = Palette(
    name="H Heuristics",
    primary=BRAND_PRIMARY,
    secondary=BRAND_SECONDARY,
    accent=BRAND_ACCENT,
    neutral_dark=BRAND_DARK,
    neutral_light=BRAND_LIGHT,
    neutral_mid=BRAND_MID,
    chart_colors=BRAND_CHART_COLORS,
    semantic=BRAND_SEMANTIC,
)

BRAND_TYPOGRAPHY = Typography(
    heading_font="Times-Bold",
    body_font="Helvetica",
    heading_weight="bold",
    body_size=10,
    heading_size_h1=20,
    heading_size_h2=14,
    heading_size_h3=11,
    caption_size=8,
    footnote_size=7,
)

BRAND_LAYOUT = Layout(
    page_width=595.27,   # A4
    page_height=841.89,
    margin_top=56.7,     # 20mm
    margin_bottom=56.7,
    margin_left=62.4,    # 22mm — slightly wider for binding
    margin_right=56.7,
    column_gap=14.0,     # 5mm
    columns=1,
)

def generate_brand_theme(seed: int | None = None) -> Theme:
    """Generate an H Heuristics brand theme with a unique cover design.

    The palette, typography, and layout are fixed to H Heuristics identity.
    The cover archetype is selected deterministically from the seed,
    ensuring each report has a unique visual identity while maintaining
    brand consistency.

    Args:
        seed: Integer seed for reproducible cover selection. Random if None.

    Returns:
        A branded Theme with a unique cover archetype.
    """
    if seed is None:
        seed = random.randint(0, 2**31 - 1)

    rng = random.Random(seed)
    archetype = rng.choice(BRAND_COVER_ARCHETYPES)
    density = rng.choice(["minimal", "moderate", "moderate", "rich"])

    return Theme(
        name=f"H Heuristics Brand (seed={seed})",
        seed=seed,
        palette=BRAND_PALETTE,
        typography=BRAND_TYPOGRAPHY,
        layout=BRAND_LAYOUT,
        cover_archetype=archetype,
        decorative_density=density,
    )


# Default instance for backwards compatibility (seed 42 = framed)
H_HEURISTICS_THEME = generate_brand_theme(seed=42)


def apply_brand(theme: Theme | None = None, seed: int | None = None) -> Theme:
    """Return the H Heuristics brand theme, optionally merging with another.

    Args:
        theme: Optional theme to merge layout params from.
        seed: Optional seed for unique cover selection. If not provided,
              uses theme.seed if theme is given, else random.

    Returns:
        Brand theme with palette and typography fixed to H Heuristics identity
        and a unique cover design based on the seed.
    """
    if seed is None and theme is not None:
        seed = theme.seed

    if theme is None:
        return generate_brand_theme(seed=seed)

    # Keep the brand identity but preserve the cover archetype from theme
    return Theme(
        name=f"H Heuristics × {theme.name}",
        seed=theme.seed,
        palette=BRAND_PALETTE,
        typography=BRAND_TYPOGRAPHY,
        layout=theme.layout,
        cover_archetype=theme.cover_archetype,
        decorative_density=theme.decorative_density,
    )
