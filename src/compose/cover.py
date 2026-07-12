"""Cover page generation — professional market research report covers.

Multiple archetypes: full_bleed, framed, split_horizontal, banded, minimal_center, geometric.
Each built with ReportLab drawing primitives for pixel-perfect output.
"""

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Flowable

from ..design.theme import Theme
from .flowables import _hex_to_rl_color


class CoverPage(Flowable):
    """A full-page cover for a market research report."""

    def __init__(self, meta: dict, theme: Theme, page_width: float, page_height: float):
        Flowable.__init__(self)
        self.meta = meta
        self.theme = theme
        self.page_w = page_width
        self.page_h = page_height
        self.width = page_width
        self.height = page_height

    def wrap(self, availWidth, availHeight):
        return (availWidth, availHeight)

    def draw(self):
        archetype = self.theme.cover_archetype
        if archetype == "full_bleed":
            self._draw_full_bleed()
        elif archetype == "framed":
            self._draw_framed()
        elif archetype == "split_horizontal":
            self._draw_split_horizontal()
        elif archetype == "banded":
            self._draw_banded()
        elif archetype == "minimal_center":
            self._draw_minimal_center()
        elif archetype == "geometric":
            self._draw_geometric()
        else:
            self._draw_full_bleed()

    def _draw_full_bleed(self):
        """Solid color background with centered white title."""
        p = self.theme.palette
        t = self.theme.typography

        # Full-page color
        bg = _hex_to_rl_color(p.primary)
        self.canv.setFillColor(bg)
        self.canv.rect(0, 0, self.page_w, self.page_h, fill=1, stroke=0)

        # Title
        self.canv.setFillColor(colors.white)
        self.canv.setFont(t.heading_font, 32)
        title = self.meta.get("title", "Report Title")
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.55, title)

        # Subtitle
        subtitle = self.meta.get("subtitle", "")
        if subtitle:
            self.canv.setFont(t.body_font, 14)
            self.canv.setFillColor(colors.Color(1, 1, 1, alpha=0.85))
            self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.48, subtitle)

        # Meta line
        date = self.meta.get("date", "")
        author = self.meta.get("author", "H Heuristics Research")
        self.canv.setFont(t.body_font, 10)
        self.canv.setFillColor(colors.Color(1, 1, 1, alpha=0.6))
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.38,
                                     f"{date}  |  {author}")

        # Brand mark
        brand = self.meta.get("brand", "H HEURISTICS")
        self.canv.setFont(t.heading_font, 11)
        self.canv.setFillColor(colors.Color(1, 1, 1, alpha=0.45))
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.12, brand)

    def _draw_framed(self):
        """White page with thick color border frame."""
        p = self.theme.palette
        t = self.theme.typography

        # White background
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_light))
        self.canv.rect(0, 0, self.page_w, self.page_h, fill=1, stroke=0)

        # Thick frame border
        frame_margin = 40
        self.canv.setStrokeColor(_hex_to_rl_color(p.primary))
        self.canv.setLineWidth(8)
        self.canv.rect(frame_margin, frame_margin,
                       self.page_w - 2 * frame_margin,
                       self.page_h - 2 * frame_margin, fill=0, stroke=1)

        # Inner thin rule
        inner_margin = frame_margin + 12
        self.canv.setStrokeColor(_hex_to_rl_color(p.secondary))
        self.canv.setLineWidth(1)
        self.canv.rect(inner_margin, inner_margin,
                       self.page_w - 2 * inner_margin,
                       self.page_h - 2 * inner_margin, fill=0, stroke=1)

        # Title
        self.canv.setFillColor(_hex_to_rl_color(p.primary))
        self.canv.setFont(t.heading_font, 30)
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.58,
                                     self.meta.get("title", "Report Title"))

        # Subtitle
        subtitle = self.meta.get("subtitle", "")
        if subtitle:
            self.canv.setFillColor(_hex_to_rl_color(p.neutral_dark))
            self.canv.setFont(t.body_font, 13)
            self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.50, subtitle)

        # Meta
        date = self.meta.get("date", "")
        self.canv.setFont(t.body_font, 10)
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_mid))
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.40,
                                     f"{date}  |  {self.meta.get('author', 'H Heuristics Research')}")

        # Brand
        self.canv.setFont(t.heading_font, 11)
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_mid))
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.10,
                                     self.meta.get("brand", "H HEURISTICS"))

    def _draw_split_horizontal(self):
        """Top 55% color block, bottom 45% white with title."""
        p = self.theme.palette
        t = self.theme.typography

        # Color block top
        bg = _hex_to_rl_color(p.primary)
        self.canv.setFillColor(bg)
        self.canv.rect(0, self.page_h * 0.45, self.page_w, self.page_h * 0.55, fill=1, stroke=0)

        # Bottom white section
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_light))
        self.canv.rect(0, 0, self.page_w, self.page_h * 0.45, fill=1, stroke=0)

        # Title on white area
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_dark))
        self.canv.setFont(t.heading_font, 28)
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.28,
                                     self.meta.get("title", "Report Title"))

        # Subtitle on white
        subtitle = self.meta.get("subtitle", "")
        if subtitle:
            self.canv.setFillColor(_hex_to_rl_color(p.neutral_mid))
            self.canv.setFont(t.body_font, 12)
            self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.21, subtitle)

        # Brand on color area
        self.canv.setFillColor(colors.Color(1, 1, 1, alpha=0.6))
        self.canv.setFont(t.heading_font, 11)
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.08,
                                     self.meta.get("brand", "H HEURISTICS"))

        # Meta on white
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_mid))
        self.canv.setFont(t.body_font, 9)
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.05,
                                     f"{self.meta.get('date', '')}")

    def _draw_banded(self):
        """Horizontal color bands with centered title."""
        p = self.theme.palette
        t = self.theme.typography

        # White bg
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_light))
        self.canv.rect(0, 0, self.page_w, self.page_h, fill=1, stroke=0)

        # Color bands
        band_h = 16
        positions = [0.65, 0.48, 0.32, 0.22]
        alphas = [0.12, 0.10, 0.08, 0.06]
        for pos, alpha in zip(positions, alphas):
            self.canv.setFillColor(_hex_to_rl_color(p.primary))
            self.canv.setStrokeColor(colors.Color(0, 0, 0, alpha=0))
            self.canv.setFillAlpha(alpha)
            self.canv.rect(0, self.page_h * pos, self.page_w, band_h, fill=1, stroke=0)
        self.canv.setFillAlpha(1)

        # Title
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_dark))
        self.canv.setFont(t.heading_font, 30)
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.55,
                                     self.meta.get("title", "Report Title"))

        # Subtitle
        subtitle = self.meta.get("subtitle", "")
        if subtitle:
            self.canv.setFillColor(_hex_to_rl_color(p.neutral_mid))
            self.canv.setFont(t.body_font, 13)
            self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.48, subtitle)

        # Meta
        self.canv.setFont(t.body_font, 9)
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.28,
                                     f"{self.meta.get('date', '')}  |  {self.meta.get('author', 'H Heuristics Research')}")

        # Brand
        self.canv.setFont(t.heading_font, 11)
        self.canv.setFillColor(_hex_to_rl_color(p.primary))
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.08,
                                     self.meta.get("brand", "H HEURISTICS"))

    def _draw_minimal_center(self):
        """Minimal white cover with thin rules and centered title."""
        p = self.theme.palette
        t = self.theme.typography

        self.canv.setFillColor(_hex_to_rl_color(p.neutral_light))
        self.canv.rect(0, 0, self.page_w, self.page_h, fill=1, stroke=0)

        # Top rule
        rule_y = self.page_h * 0.65
        rule_w = 120
        self.canv.setStrokeColor(_hex_to_rl_color(p.primary))
        self.canv.setLineWidth(2)
        self.canv.line(self.page_w / 2 - rule_w / 2, rule_y,
                       self.page_w / 2 + rule_w / 2, rule_y)

        # Title
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_dark))
        self.canv.setFont(t.heading_font, 28)
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.55,
                                     self.meta.get("title", "Report Title"))

        # Subtitle
        subtitle = self.meta.get("subtitle", "")
        if subtitle:
            self.canv.setFillColor(_hex_to_rl_color(p.neutral_mid))
            self.canv.setFont(t.body_font, 12)
            self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.49, subtitle)

        # Bottom rule
        self.canv.setStrokeColor(_hex_to_rl_color(p.secondary))
        self.canv.setLineWidth(1.5)
        self.canv.line(self.page_w / 2 - rule_w / 2, self.page_h * 0.43,
                       self.page_w / 2 + rule_w / 2, self.page_h * 0.43)

        # Meta
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_mid))
        self.canv.setFont(t.body_font, 9)
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.35,
                                     f"{self.meta.get('date', '')}")

        # Brand bottom
        self.canv.setFont(t.heading_font, 11)
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.08,
                                     self.meta.get("brand", "H HEURISTICS"))

    def _draw_geometric(self):
        """Geometric abstract shapes with centered title."""
        p = self.theme.palette
        t = self.theme.typography

        # White bg
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_light))
        self.canv.rect(0, 0, self.page_w, self.page_h, fill=1, stroke=0)

        # Geometric shapes
        import math
        # Large circle top-right
        self.canv.setFillColor(_hex_to_rl_color(p.primary))
        self.canv.setFillAlpha(0.08)
        self.canv.circle(self.page_w * 0.8, self.page_h * 0.75, 120, fill=1, stroke=0)

        # Smaller circle bottom-left
        self.canv.setFillAlpha(0.06)
        self.canv.circle(self.page_w * 0.15, self.page_h * 0.2, 80, fill=1, stroke=0)

        # Diamond shape
        self.canv.setFillAlpha(0.10)
        path = self.canv.beginPath()
        cx, cy = self.page_w * 0.5, self.page_h * 0.65
        path.moveTo(cx, cy + 60)
        path.lineTo(cx + 45, cy)
        path.lineTo(cx, cy - 60)
        path.lineTo(cx - 45, cy)
        path.close()
        self.canv.drawPath(path, fill=1, stroke=0)
        self.canv.setFillAlpha(1)

        # Title
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_dark))
        self.canv.setFont(t.heading_font, 30)
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.55,
                                     self.meta.get("title", "Report Title"))

        # Subtitle
        subtitle = self.meta.get("subtitle", "")
        if subtitle:
            self.canv.setFillColor(_hex_to_rl_color(p.neutral_mid))
            self.canv.setFont(t.body_font, 13)
            self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.48, subtitle)

        # Meta
        self.canv.setFont(t.body_font, 10)
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.30,
                                     f"{self.meta.get('date', '')}  |  {self.meta.get('author', 'H Heuristics Research')}")

        # Brand
        self.canv.setFont(t.heading_font, 11)
        self.canv.setFillColor(_hex_to_rl_color(p.primary))
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.08,
                                     self.meta.get("brand", "H HEURISTICS"))
