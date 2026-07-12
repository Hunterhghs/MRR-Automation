"""Typography system — font registration and pairing for ReportLab PDF.

Uses bundled or system fonts registered via reportlab.pdfbase.pdfmetrics.
No Google Fonts dependency — all fonts registered locally for offline PDF generation.
"""

import os
import random
from dataclasses import dataclass
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


@dataclass
class Typography:
    """Font configuration for a report."""
    heading_font: str       # Registered font name for headings
    body_font: str          # Registered font name for body text
    heading_weight: str     # "bold" or "normal"
    body_size: int          # Base body font size in points
    heading_size_h1: int    # Chapter title size
    heading_size_h2: int    # Section title size
    heading_size_h3: int    # Subsection title size
    caption_size: int       # Chart/table caption size
    footnote_size: int      # Footer/disclaimer size

    @property
    def body_leading(self) -> float:
        """Line spacing multiplier."""
        return self.body_size * 1.55


FONT_DIR = Path(__file__).parent / "fonts"

# Font search paths
_FONT_SEARCH_PATHS = [
    FONT_DIR,
    Path("/System/Library/Fonts"),
    Path("/Library/Fonts"),
    Path("/usr/share/fonts"),
    Path.home() / "Library" / "Fonts",
]

# Registry of registered fonts
_REGISTERED = set()


def _find_font_file(name_hints: list[str]) -> str | None:
    """Search for a font file across system and bundled paths."""
    for hint in name_hints:
        for search_path in _FONT_SEARCH_PATHS:
            if not search_path.exists():
                continue
            # Exact match
            for ext in [".ttf", ".otf", ".ttc"]:
                candidate = search_path / f"{hint}{ext}"
                if candidate.exists():
                    return str(candidate)
            # Case-insensitive glob
            for f in search_path.glob("*.ttf"):
                if hint.lower() in f.stem.lower():
                    return str(f)
            for f in search_path.glob("*.otf"):
                if hint.lower() in f.stem.lower():
                    return str(f)
    return None


def register_font(family: str, bold: bool = False, italic: bool = False) -> str:
    """Register a font with ReportLab, searching system paths.

    Returns the registered font name (may differ from family).
    """
    key = f"{family}_{bold}_{italic}"
    if key in _REGISTERED:
        return family

    # Try to find the font file
    variants = [family]
    if bold:
        variants = [f"{family}-Bold", f"{family}Bold", f"{family}_Bold"] + variants
    if italic:
        variants = [f"{family}-Italic", f"{family}Italic", f"{family}_Italic"] + variants
    if bold and italic:
        variants = [f"{family}-BoldItalic", f"{family}BoldItalic"] + variants

    font_path = _find_font_file(variants)

    if font_path:
        try:
            pdfmetrics.registerFont(TTFont(family, font_path))
            _REGISTERED.add(key)
            return family
        except Exception:
            pass

    # Fallback: use built-in Helvetica equivalents
    if family not in _REGISTERED and not any(f.startswith(family) for f in _REGISTERED):
        _REGISTERED.add(key)

    return family


def register_default_fonts():
    """Register a robust set of fonts for PDF generation.

    Tries system fonts first, falls back to ReportLab built-ins.
    """
    # Always register Times-Roman and Helvetica equivalents
    # These are built into ReportLab and always available

    # Try to register nice system fonts
    serif_families = [
        "Times New Roman", "Georgia", "Palatino", "Book Antiqua",
        "Baskerville", "Garamond", "Caslon",
    ]
    sans_families = [
        "Helvetica", "Arial", "Inter", "SF Pro Display", "SF Pro Text",
        "Calibri", "Segoe UI", "Open Sans", "Lato", "Roboto",
    ]

    for fam in serif_families + sans_families:
        register_font(fam)
        register_font(fam, bold=True)
        register_font(fam, italic=True)


# ── Curated pairings for ReportLab ─────────────────────────────────────

# ReportLab built-in font names (always available)
# Serif: Times-Roman, Times-Bold, Times-Italic, Times-BoldItalic
# Sans:  Helvetica, Helvetica-Bold, Helvetica-Oblique, Helvetica-BoldOblique

FONT_PAIRINGS = [
    {
        "heading_font": "Times-Bold",
        "body_font": "Helvetica",
        "heading_weight": "bold",
    },
    {
        "heading_font": "Times-Bold",
        "body_font": "Times-Roman",
        "heading_weight": "bold",
    },
    {
        "heading_font": "Helvetica-Bold",
        "body_font": "Times-Roman",
        "heading_weight": "bold",
    },
    {
        "heading_font": "Helvetica-Bold",
        "body_font": "Helvetica",
        "heading_weight": "bold",
    },
    {
        "heading_font": "Times-Bold",
        "body_font": "Helvetica",
        "heading_weight": "bold",
    },
    {
        "heading_font": "Helvetica-Bold",
        "body_font": "Times-Roman",
        "heading_weight": "bold",
    },
]


def generate_typography(seed: int) -> Typography:
    """Pick a font pairing deterministically from the seed.

    Args:
        seed: Integer seed for reproducibility.

    Returns:
        A Typography with heading and body font specifications.
    """
    rng = random.Random(seed)
    idx = rng.randint(0, len(FONT_PAIRINGS) - 1)
    pairing = FONT_PAIRINGS[idx]

    return Typography(
        heading_font=pairing["heading_font"],
        body_font=pairing["body_font"],
        heading_weight=pairing["heading_weight"],
        body_size=10,
        heading_size_h1=20,
        heading_size_h2=14,
        heading_size_h3=11,
        caption_size=8,
        footnote_size=7,
    )
