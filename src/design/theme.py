"""Theme generation — bundles palette, typography, and layout into a Theme object."""

import random
from dataclasses import dataclass

from .palette import generate_palette, Palette
from .typography import generate_typography, Typography


COVER_ARCHETYPES = [
    "full_bleed",
    "split_horizontal",
    "framed",
    "minimal_center",
    "banded",
    "geometric",
    "corner_bracket",
    "sidebar",
    "gradient_overlay",
    "window",
    "vertical_split",
]


@dataclass
class Layout:
    """Page layout parameters in points (1pt = 1/72 inch)."""
    page_width: float
    page_height: float
    margin_top: float
    margin_bottom: float
    margin_left: float
    margin_right: float
    column_gap: float
    columns: int = 1

    @property
    def content_width(self) -> float:
        return self.page_width - self.margin_left - self.margin_right

    @property
    def content_height(self) -> float:
        return self.page_height - self.margin_top - self.margin_bottom

    @property
    def column_width(self) -> float:
        if self.columns <= 1:
            return self.content_width
        return (self.content_width - self.column_gap * (self.columns - 1)) / self.columns


@dataclass
class Theme:
    """Complete visual theme for a report."""
    name: str
    seed: int
    palette: Palette
    typography: Typography
    layout: Layout
    cover_archetype: str
    decorative_density: str  # "minimal", "moderate", "rich"


def generate_theme(seed: int | None = None, page_size: str = "A4") -> Theme:
    """Generate a unique visual theme for a report.

    Args:
        seed: Integer for reproducibility. Random if None.
        page_size: "A4" (595.27×841.89pt) or "US Letter" (612×792pt).

    Returns:
        A fully-specified Theme.
    """
    if seed is None:
        seed = random.randint(0, 2**31 - 1)

    rng = random.Random(seed)
    theme_name = f"Theme-{seed:08x}"

    palette = generate_palette(seed, name=theme_name)
    typography = generate_typography(seed)

    if page_size == "US Letter":
        pw, ph = 612.0, 792.0
    else:
        pw, ph = 595.27, 841.89  # A4

    # Professional margins: 18–24mm = ~51–68pt
    margin_variants = [
        (56.7, 56.7, 56.7, 56.7),   # 20mm even
        (62.4, 56.7, 51.0, 51.0),   # generous top
        (56.7, 51.0, 62.4, 62.4),   # generous bottom
        (51.0, 51.0, 70.9, 70.9),   # wide sides
        (56.7, 62.4, 56.7, 56.7),   # generous bottom
    ]
    mt, mb, ml, mr = margin_variants[rng.randint(0, len(margin_variants) - 1)]

    layout = Layout(
        page_width=pw,
        page_height=ph,
        margin_top=mt,
        margin_bottom=mb,
        margin_left=ml,
        margin_right=mr,
        column_gap=14.0,  # 5mm
        columns=1,
    )

    cover = COVER_ARCHETYPES[rng.randint(0, len(COVER_ARCHETYPES) - 1)]
    density = rng.choice(["minimal", "minimal", "moderate", "moderate", "rich"])

    return Theme(
        name=theme_name,
        seed=seed,
        palette=palette,
        typography=typography,
        layout=layout,
        cover_archetype=cover,
        decorative_density=density,
    )
