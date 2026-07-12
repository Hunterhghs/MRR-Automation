"""H Heuristics brand identity — fixed brand theme for all reports.

This overrides the algorithmic theme generation when the brand flag is set.
Colors match H Heuristics visual identity: professional, authoritative,
with a warm academic feel suitable for market research.
"""

from .palette import Palette
from .typography import Typography
from .theme import Theme, Layout

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

H_HEURISTICS_THEME = Theme(
    name="H Heuristics Brand",
    seed=42,
    palette=BRAND_PALETTE,
    typography=BRAND_TYPOGRAPHY,
    layout=BRAND_LAYOUT,
    cover_archetype="framed",
    decorative_density="moderate",
)


def apply_brand(theme: Theme | None = None) -> Theme:
    """Return the H Heuristics brand theme, optionally merging with another.

    Args:
        theme: Optional theme to merge layout params from.

    Returns:
        Brand theme with palette and typography fixed to H Heuristics identity.
    """
    if theme is None:
        return H_HEURISTICS_THEME

    # Keep the brand identity but allow different layouts/cover styles
    return Theme(
        name=f"H Heuristics × {theme.name}",
        seed=theme.seed,
        palette=BRAND_PALETTE,
        typography=BRAND_TYPOGRAPHY,
        layout=theme.layout,
        cover_archetype=theme.cover_archetype,
        decorative_density=theme.decorative_density,
    )
