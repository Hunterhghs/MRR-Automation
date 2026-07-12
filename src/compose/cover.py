"""Cover page generation — professional market research report covers.

Multiple archetypes: full_bleed, framed, split_horizontal, banded, minimal_center, geometric.
Each built with ReportLab drawing primitives for pixel-perfect output.
All titles use adaptive font sizing via stringWidth measurement to prevent overflow.
"""

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Flowable
from reportlab.pdfbase.pdfmetrics import stringWidth

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

    def _fit_title(self, title: str, max_width_pt: float, max_font: int = 32,
                   min_font: int = 16) -> tuple[int, float]:
        """Return (font_size, text_width) that fits within max_width_pt."""
        t = self.theme.typography
        fs = max_font
        while fs >= min_font:
            w = stringWidth(title, t.heading_font, fs)
            if w <= max_width_pt:
                return fs, w
            fs -= 2
        return min_font, stringWidth(title, t.heading_font, min_font)

    def _fit_subtitle(self, subtitle: str, max_width_pt: float, max_font: int = 14,
                      min_font: int = 9) -> tuple[int, float]:
        """Return (font_size, text_width) that fits."""
        t = self.theme.typography
        fs = max_font
        while fs >= min_font:
            w = stringWidth(subtitle, t.body_font, fs)
            if w <= max_width_pt:
                return fs, w
            fs -= 1
        return min_font, stringWidth(subtitle, t.body_font, min_font)

    def draw(self):
        archetype = self.theme.cover_archetype
        dispatch = {
            "full_bleed": self._draw_full_bleed,
            "framed": self._draw_framed,
            "split_horizontal": self._draw_split_horizontal,
            "banded": self._draw_banded,
            "minimal_center": self._draw_minimal_center,
            "geometric": self._draw_geometric,
            "corner_bracket": self._draw_corner_bracket,
            "sidebar": self._draw_sidebar,
            "gradient_overlay": self._draw_gradient_overlay,
            "window": self._draw_window,
            "vertical_split": self._draw_vertical_split,
        }
        dispatch.get(archetype, self._draw_full_bleed)()

    def _draw_full_bleed(self):
        """Solid color background with centered white title."""
        p = self.theme.palette
        t = self.theme.typography

        bg = _hex_to_rl_color(p.primary)
        self.canv.setFillColor(bg)
        self.canv.rect(0, 0, self.page_w, self.page_h, fill=1, stroke=0)

        title = self.meta.get("title", "Report Title")
        max_w = self.page_w * 0.85
        fs, _ = self._fit_title(title, max_w)
        self.canv.setFillColor(colors.white)
        self.canv.setFont(t.heading_font, fs)
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.58, title)

        subtitle = self.meta.get("subtitle", "")
        if subtitle:
            sfs, _ = self._fit_subtitle(subtitle, max_w)
            self.canv.setFont(t.body_font, sfs)
            self.canv.setFillColor(colors.Color(1, 1, 1, alpha=0.85))
            self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.50, subtitle)

        date = self.meta.get("date", "")
        author = self.meta.get("author", "H Heuristics Research")
        self.canv.setFont(t.body_font, 10)
        self.canv.setFillColor(colors.Color(1, 1, 1, alpha=0.6))
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.38,
                                     f"{date}  |  {author}")

        brand = self.meta.get("brand", "H HEURISTICS")
        self.canv.setFont(t.heading_font, 11)
        self.canv.setFillColor(colors.Color(1, 1, 1, alpha=0.45))
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.10, brand)

    def _draw_framed(self):
        """White page with thick color border frame."""
        p = self.theme.palette
        t = self.theme.typography

        self.canv.setFillColor(_hex_to_rl_color(p.neutral_light))
        self.canv.rect(0, 0, self.page_w, self.page_h, fill=1, stroke=0)

        frame_margin = 40
        self.canv.setStrokeColor(_hex_to_rl_color(p.primary))
        self.canv.setLineWidth(8)
        self.canv.rect(frame_margin, frame_margin,
                       self.page_w - 2 * frame_margin,
                       self.page_h - 2 * frame_margin, fill=0, stroke=1)

        inner_margin = frame_margin + 12
        self.canv.setStrokeColor(_hex_to_rl_color(p.secondary))
        self.canv.setLineWidth(1)
        self.canv.rect(inner_margin, inner_margin,
                       self.page_w - 2 * inner_margin,
                       self.page_h - 2 * inner_margin, fill=0, stroke=1)

        title = self.meta.get("title", "Report Title")
        max_w = self.page_w - 2 * inner_margin - 40
        fs, _ = self._fit_title(title, max_w, max_font=30)
        self.canv.setFillColor(_hex_to_rl_color(p.primary))
        self.canv.setFont(t.heading_font, fs)
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.58, title)

        subtitle = self.meta.get("subtitle", "")
        if subtitle:
            sfs, _ = self._fit_subtitle(subtitle, max_w)
            self.canv.setFillColor(_hex_to_rl_color(p.neutral_dark))
            self.canv.setFont(t.body_font, sfs)
            self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.50, subtitle)

        date = self.meta.get("date", "")
        self.canv.setFont(t.body_font, 10)
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_mid))
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.40,
                                     f"{date}  |  {self.meta.get('author', 'H Heuristics Research')}")

        self.canv.setFont(t.heading_font, 11)
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_mid))
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.10,
                                     self.meta.get("brand", "H HEURISTICS"))

    def _draw_split_horizontal(self):
        """Top 55% color block, bottom 45% white with title."""
        p = self.theme.palette
        t = self.theme.typography

        bg = _hex_to_rl_color(p.primary)
        self.canv.setFillColor(bg)
        self.canv.rect(0, self.page_h * 0.45, self.page_w, self.page_h * 0.55, fill=1, stroke=0)

        self.canv.setFillColor(_hex_to_rl_color(p.neutral_light))
        self.canv.rect(0, 0, self.page_w, self.page_h * 0.45, fill=1, stroke=0)

        title = self.meta.get("title", "Report Title")
        max_w = self.page_w * 0.85
        fs, _ = self._fit_title(title, max_w, max_font=28)
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_dark))
        self.canv.setFont(t.heading_font, fs)
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.28, title)

        subtitle = self.meta.get("subtitle", "")
        if subtitle:
            sfs, _ = self._fit_subtitle(subtitle, max_w)
            self.canv.setFillColor(_hex_to_rl_color(p.neutral_mid))
            self.canv.setFont(t.body_font, sfs)
            self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.21, subtitle)

        self.canv.setFillColor(colors.Color(1, 1, 1, alpha=0.6))
        self.canv.setFont(t.heading_font, 11)
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.08,
                                     self.meta.get("brand", "H HEURISTICS"))

        self.canv.setFillColor(_hex_to_rl_color(p.neutral_mid))
        self.canv.setFont(t.body_font, 9)
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.05,
                                     self.meta.get("date", ""))

    def _draw_banded(self):
        """Horizontal color bands with centered title."""
        p = self.theme.palette
        t = self.theme.typography

        self.canv.setFillColor(_hex_to_rl_color(p.neutral_light))
        self.canv.rect(0, 0, self.page_w, self.page_h, fill=1, stroke=0)

        band_h = 16
        positions = [0.65, 0.48, 0.32, 0.22]
        alphas = [0.12, 0.10, 0.08, 0.06]
        for pos, alpha in zip(positions, alphas):
            self.canv.setFillColor(_hex_to_rl_color(p.primary))
            self.canv.setFillAlpha(alpha)
            self.canv.rect(0, self.page_h * pos, self.page_w, band_h, fill=1, stroke=0)
        self.canv.setFillAlpha(1)

        title = self.meta.get("title", "Report Title")
        max_w = self.page_w * 0.80
        fs, _ = self._fit_title(title, max_w, max_font=30)
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_dark))
        self.canv.setFont(t.heading_font, fs)
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.55, title)

        subtitle = self.meta.get("subtitle", "")
        if subtitle:
            sfs, _ = self._fit_subtitle(subtitle, max_w)
            self.canv.setFillColor(_hex_to_rl_color(p.neutral_mid))
            self.canv.setFont(t.body_font, sfs)
            self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.48, subtitle)

        self.canv.setFont(t.body_font, 9)
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.28,
                                     f"{self.meta.get('date', '')}  |  {self.meta.get('author', 'H Heuristics Research')}")

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

        rule_y = self.page_h * 0.65
        rule_w = 120
        self.canv.setStrokeColor(_hex_to_rl_color(p.primary))
        self.canv.setLineWidth(2)
        self.canv.line(self.page_w / 2 - rule_w / 2, rule_y,
                       self.page_w / 2 + rule_w / 2, rule_y)

        title = self.meta.get("title", "Report Title")
        max_w = self.page_w * 0.80
        fs, _ = self._fit_title(title, max_w, max_font=28)
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_dark))
        self.canv.setFont(t.heading_font, fs)
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.55, title)

        subtitle = self.meta.get("subtitle", "")
        if subtitle:
            sfs, _ = self._fit_subtitle(subtitle, max_w)
            self.canv.setFillColor(_hex_to_rl_color(p.neutral_mid))
            self.canv.setFont(t.body_font, sfs)
            self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.49, subtitle)

        self.canv.setStrokeColor(_hex_to_rl_color(p.secondary))
        self.canv.setLineWidth(1.5)
        self.canv.line(self.page_w / 2 - rule_w / 2, self.page_h * 0.43,
                       self.page_w / 2 + rule_w / 2, self.page_h * 0.43)

        self.canv.setFillColor(_hex_to_rl_color(p.neutral_mid))
        self.canv.setFont(t.body_font, 9)
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.35,
                                     self.meta.get("date", ""))

        self.canv.setFont(t.heading_font, 11)
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.08,
                                     self.meta.get("brand", "H HEURISTICS"))

    def _draw_geometric(self):
        """Geometric abstract shapes with centered title."""
        p = self.theme.palette
        t = self.theme.typography

        self.canv.setFillColor(_hex_to_rl_color(p.neutral_light))
        self.canv.rect(0, 0, self.page_w, self.page_h, fill=1, stroke=0)

        # Subtle geometric shapes
        import math
        self.canv.setFillColor(_hex_to_rl_color(p.primary))
        self.canv.setFillAlpha(0.08)
        self.canv.circle(self.page_w * 0.8, self.page_h * 0.75, 120, fill=1, stroke=0)
        self.canv.setFillAlpha(0.06)
        self.canv.circle(self.page_w * 0.15, self.page_h * 0.2, 80, fill=1, stroke=0)
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

        title = self.meta.get("title", "Report Title")
        max_w = self.page_w * 0.80
        fs, _ = self._fit_title(title, max_w, max_font=30)
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_dark))
        self.canv.setFont(t.heading_font, fs)
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.55, title)

        subtitle = self.meta.get("subtitle", "")
        if subtitle:
            sfs, _ = self._fit_subtitle(subtitle, max_w)
            self.canv.setFillColor(_hex_to_rl_color(p.neutral_mid))
            self.canv.setFont(t.body_font, sfs)
            self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.48, subtitle)

        self.canv.setFont(t.body_font, 10)
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.30,
                                     f"{self.meta.get('date', '')}  |  {self.meta.get('author', 'H Heuristics Research')}")

        self.canv.setFont(t.heading_font, 11)
        self.canv.setFillColor(_hex_to_rl_color(p.primary))
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.08,
                                     self.meta.get("brand", "H HEURISTICS"))

    # ── NEW ARCHETYPES ─────────────────────────────────────────────

    def _draw_corner_bracket(self):
        """L-shaped brackets in corners framing centered title — elegant and architectural."""
        p = self.theme.palette
        t = self.theme.typography

        self.canv.setFillColor(_hex_to_rl_color(p.neutral_light))
        self.canv.rect(0, 0, self.page_w, self.page_h, fill=1, stroke=0)

        bracket_len = 55
        bracket_thick = 5
        margin = 45
        self.canv.setStrokeColor(_hex_to_rl_color(p.primary))
        self.canv.setLineWidth(bracket_thick)
        self.canv.setLineCap(1)

        corners = [
            (margin, margin, 1, 1),
            (self.page_w - margin, margin, -1, 1),
            (margin, self.page_h - margin, 1, -1),
            (self.page_w - margin, self.page_h - margin, -1, -1),
        ]
        for cx, cy, dx, dy in corners:
            self.canv.line(cx, cy, cx + dx * bracket_len, cy)
            self.canv.line(cx, cy, cx, cy + dy * bracket_len)

        title = self.meta.get("title", "Report Title")
        max_w = self.page_w - 2 * margin - 40
        fs, _ = self._fit_title(title, max_w, max_font=28)
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_dark))
        self.canv.setFont(t.heading_font, fs)
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.58, title)

        subtitle = self.meta.get("subtitle", "")
        if subtitle:
            sfs, _ = self._fit_subtitle(subtitle, max_w)
            self.canv.setFillColor(_hex_to_rl_color(p.neutral_mid))
            self.canv.setFont(t.body_font, sfs)
            self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.50, subtitle)

        self.canv.setFont(t.body_font, 10)
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_mid))
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.38,
                                     f"{self.meta.get('date', '')}  |  {self.meta.get('author', 'H Heuristics Research')}")

        self.canv.setFont(t.heading_font, 11)
        self.canv.setFillColor(_hex_to_rl_color(p.primary))
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.08,
                                     self.meta.get("brand", "H HEURISTICS"))

    def _draw_sidebar(self):
        """Left 35% color panel with title and meta on right 65% — editorial layout."""
        p = self.theme.palette
        t = self.theme.typography

        self.canv.setFillColor(_hex_to_rl_color(p.neutral_light))
        self.canv.rect(0, 0, self.page_w, self.page_h, fill=1, stroke=0)

        sidebar_w = self.page_w * 0.35
        self.canv.setFillColor(_hex_to_rl_color(p.primary))
        self.canv.rect(0, 0, sidebar_w, self.page_h, fill=1, stroke=0)

        self.canv.setFillColor(colors.Color(1, 1, 1, alpha=0.5))
        self.canv.setFont(t.heading_font, 10)
        brand = self.meta.get("brand", "H HEURISTICS")
        self.canv.drawCentredString(sidebar_w / 2, self.page_h * 0.12, brand)

        self.canv.setStrokeColor(_hex_to_rl_color(p.secondary))
        self.canv.setLineWidth(1)
        self.canv.line(sidebar_w + 15, self.page_h * 0.35, sidebar_w + 15, self.page_h * 0.65)

        content_x = sidebar_w + 35
        title = self.meta.get("title", "Report Title")
        max_w = self.page_w - content_x - 40
        fs, _ = self._fit_title(title, max_w, max_font=26)
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_dark))
        self.canv.setFont(t.heading_font, fs)
        self.canv.drawString(content_x, self.page_h * 0.58, title)

        subtitle = self.meta.get("subtitle", "")
        if subtitle:
            sfs, _ = self._fit_subtitle(subtitle, max_w)
            self.canv.setFillColor(_hex_to_rl_color(p.neutral_mid))
            self.canv.setFont(t.body_font, sfs)
            self.canv.drawString(content_x, self.page_h * 0.50, subtitle)

        self.canv.setFont(t.body_font, 9)
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_mid))
        self.canv.drawString(content_x, self.page_h * 0.38,
                             f"{self.meta.get('date', '')}  |  {self.meta.get('author', 'H Heuristics Research')}")

    def _draw_gradient_overlay(self):
        """Subtle gradient bands creating depth with centered title — sophisticated and modern."""
        p = self.theme.palette
        t = self.theme.typography

        self.canv.setFillColor(_hex_to_rl_color(p.primary))
        self.canv.rect(0, 0, self.page_w, self.page_h, fill=1, stroke=0)

        n_bands = 40
        band_h = self.page_h / n_bands
        for i in range(n_bands):
            alpha = 0.03 * (1 - abs(i - n_bands / 2) / (n_bands / 2))
            self.canv.setFillColor(colors.Color(1, 1, 1, alpha=alpha))
            self.canv.rect(0, i * band_h, self.page_w, band_h + 1, fill=1, stroke=0)

        self.canv.setStrokeColor(_hex_to_rl_color(p.secondary))
        self.canv.setLineWidth(2)
        rule_y = self.page_h * 0.47
        self.canv.line(self.page_w * 0.30, rule_y, self.page_w * 0.70, rule_y)

        title = self.meta.get("title", "Report Title")
        max_w = self.page_w * 0.85
        fs, _ = self._fit_title(title, max_w)
        self.canv.setFillColor(colors.white)
        self.canv.setFont(t.heading_font, fs)
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.58, title)

        subtitle = self.meta.get("subtitle", "")
        if subtitle:
            sfs, _ = self._fit_subtitle(subtitle, max_w)
            self.canv.setFillColor(colors.Color(1, 1, 1, alpha=0.80))
            self.canv.setFont(t.body_font, sfs)
            self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.44, subtitle)

        self.canv.setFont(t.body_font, 10)
        self.canv.setFillColor(colors.Color(1, 1, 1, alpha=0.55))
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.35,
                                     f"{self.meta.get('date', '')}  |  {self.meta.get('author', 'H Heuristics Research')}")

        brand = self.meta.get("brand", "H HEURISTICS")
        self.canv.setFont(t.heading_font, 11)
        self.canv.setFillColor(colors.Color(1, 1, 1, alpha=0.40))
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.08, brand)

    def _draw_window(self):
        """Central rounded color panel floating on white — clean and modern."""
        p = self.theme.palette
        t = self.theme.typography

        self.canv.setFillColor(_hex_to_rl_color(p.neutral_light))
        self.canv.rect(0, 0, self.page_w, self.page_h, fill=1, stroke=0)

        win_w = self.page_w * 0.65
        win_h = self.page_h * 0.40
        win_x = (self.page_w - win_w) / 2
        win_y = (self.page_h - win_h) / 2 + 20

        self.canv.setFillColor(_hex_to_rl_color(p.primary))
        self.canv.roundRect(win_x, win_y, win_w, win_h, 12, fill=1, stroke=0)

        self.canv.setStrokeColor(_hex_to_rl_color(p.secondary))
        self.canv.setLineWidth(1)
        self.canv.roundRect(win_x + 8, win_y + 8, win_w - 16, win_h - 16, 8, fill=0, stroke=1)

        title = self.meta.get("title", "Report Title")
        max_w = win_w - 60
        fs, _ = self._fit_title(title, max_w, max_font=26)
        self.canv.setFillColor(colors.white)
        self.canv.setFont(t.heading_font, fs)
        self.canv.drawCentredString(self.page_w / 2, win_y + win_h * 0.62, title)

        subtitle = self.meta.get("subtitle", "")
        if subtitle:
            sfs, _ = self._fit_subtitle(subtitle, max_w)
            self.canv.setFillColor(colors.Color(1, 1, 1, alpha=0.80))
            self.canv.setFont(t.body_font, sfs)
            self.canv.drawCentredString(self.page_w / 2, win_y + win_h * 0.42, subtitle)

        self.canv.setFont(t.body_font, 10)
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_mid))
        self.canv.drawCentredString(self.page_w / 2, win_y - 30,
                                     f"{self.meta.get('date', '')}  |  {self.meta.get('author', 'H Heuristics Research')}")

        self.canv.setFont(t.heading_font, 11)
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_mid))
        self.canv.drawCentredString(self.page_w / 2, self.page_h * 0.08,
                                     self.meta.get("brand", "H HEURISTICS"))

    def _draw_vertical_split(self):
        """Vertical split — left 45% color, right 55% white with left-aligned title on color side."""
        p = self.theme.palette
        t = self.theme.typography

        split_x = self.page_w * 0.45
        self.canv.setFillColor(_hex_to_rl_color(p.primary))
        self.canv.rect(0, 0, split_x, self.page_h, fill=1, stroke=0)

        self.canv.setFillColor(_hex_to_rl_color(p.neutral_light))
        self.canv.rect(split_x, 0, self.page_w - split_x, self.page_h, fill=1, stroke=0)

        self.canv.setStrokeColor(_hex_to_rl_color(p.secondary))
        self.canv.setLineWidth(1.5)
        self.canv.line(split_x, self.page_h * 0.30, split_x, self.page_h * 0.70)

        title = self.meta.get("title", "Report Title")
        max_w = split_x - 50
        fs, _ = self._fit_title(title, max_w, max_font=26)
        self.canv.setFillColor(colors.white)
        self.canv.setFont(t.heading_font, fs)
        self.canv.drawString(35, self.page_h * 0.58, title)

        subtitle = self.meta.get("subtitle", "")
        if subtitle:
            sfs, _ = self._fit_subtitle(subtitle, max_w)
            self.canv.setFillColor(colors.Color(1, 1, 1, alpha=0.80))
            self.canv.setFont(t.body_font, sfs)
            self.canv.drawString(35, self.page_h * 0.50, subtitle)

        self.canv.setFont(t.body_font, 10)
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_mid))
        self.canv.drawCentredString(split_x + (self.page_w - split_x) / 2, self.page_h * 0.38,
                                     f"{self.meta.get('date', '')}  |  {self.meta.get('author', 'H Heuristics Research')}")

        self.canv.setFont(t.heading_font, 10)
        self.canv.setFillColor(colors.Color(1, 1, 1, alpha=0.45))
        self.canv.drawString(35, self.page_h * 0.08, self.meta.get("brand", "H HEURISTICS"))
