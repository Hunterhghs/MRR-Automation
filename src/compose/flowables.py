"""Custom ReportLab flowables for professional market research reports.

Includes: KPI cards, callout boxes, key findings panels, case study blocks,
SWOT matrices, timeline graphics, section dividers, and branded elements.
"""

from reportlab.lib import colors
from reportlab.lib.units import inch, mm, cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    Flowable, Paragraph, Table, TableStyle, Spacer, Image,
    KeepTogether, HRFlowable,
)
from reportlab.pdfbase.pdfmetrics import stringWidth
from io import BytesIO

from ..design.theme import Theme


# ── Color helpers ──────────────────────────────────────────────────────

def _hex_to_rl_color(hex_str: str) -> colors.Color:
    """Convert hex string to ReportLab Color."""
    hex_str = hex_str.lstrip("#")
    r = int(hex_str[0:2], 16) / 255.0
    g = int(hex_str[2:4], 16) / 255.0
    b = int(hex_str[4:6], 16) / 255.0
    return colors.Color(r, g, b)


# ── Base styled paragraph helpers ──────────────────────────────────────

def body_style(theme: Theme, size: int | None = None, bold: bool = False,
               align: int = TA_JUSTIFY, leading: float | None = None) -> ParagraphStyle:
    """Standard body paragraph style."""
    t = theme.typography
    sz = size or t.body_size
    ld = leading or (sz * 1.55)
    return ParagraphStyle(
        "Body", fontName=t.body_font, fontSize=sz,
        leading=ld, textColor=_hex_to_rl_color(theme.palette.neutral_dark),
        alignment=align, spaceAfter=4 if not bold else 6,
        spaceBefore=0 if not bold else 4,
    )


def heading_style(theme: Theme, level: int = 1) -> ParagraphStyle:
    """Heading style for chapter/section titles."""
    t = theme.typography
    p = theme.palette
    if level == 1:
        sz = t.heading_size_h1
        color = p.primary
        space_before = 0
        space_after = 8
    elif level == 2:
        sz = t.heading_size_h2
        color = p.secondary
        space_before = 12
        space_after = 6
    else:
        sz = t.heading_size_h3
        color = p.neutral_dark
        space_before = 8
        space_after = 4

    return ParagraphStyle(
        f"Heading{level}", fontName=t.heading_font,
        fontSize=sz, leading=sz * 1.25,
        textColor=_hex_to_rl_color(color),
        spaceBefore=space_before, spaceAfter=space_after,
        bold=(t.heading_weight == "bold"),
    )


def caption_style(theme: Theme) -> ParagraphStyle:
    """Figure/table caption style."""
    t = theme.typography
    p = theme.palette
    return ParagraphStyle(
        "Caption", fontName=t.body_font,
        fontSize=t.caption_size, leading=t.caption_size * 1.3,
        textColor=_hex_to_rl_color(p.neutral_mid),
        alignment=TA_CENTER, spaceAfter=4, fontStyle="italic",
    )


# ── Flowable: SectionDivider ──────────────────────────────────────────

class SectionDivider(Flowable):
    """A horizontal rule divider between sections."""
    def __init__(self, theme: Theme, thickness: float = 1.5):
        Flowable.__init__(self)
        self.theme = theme
        self.thickness = thickness
        self.width = 0  # Will be set by wrap
        self.height = thickness + 10  # Rule + padding

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        return (availWidth, self.height)

    def draw(self):
        color = _hex_to_rl_color(self.theme.palette.primary)
        self.canv.setStrokeColor(color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 5, self.width, 5)


# ── Flowable: KPICards ────────────────────────────────────────────────

class KPICards(Flowable):
    """A row of KPI metric cards (2-4 per row)."""
    def __init__(self, kpi_items: list[dict], theme: Theme, cols: int = 3):
        Flowable.__init__(self)
        self.items = kpi_items
        self.theme = theme
        self.cols = min(cols, len(kpi_items))
        self.card_padding = 10
        self.card_height = 65

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        rows = (len(self.items) + self.cols - 1) // self.cols
        self.height = rows * (self.card_height + 6) + 4
        return (availWidth, self.height)

    def draw(self):
        p = self.theme.palette
        t = self.theme.typography
        card_w = (self.width - (self.cols - 1) * 6) / self.cols

        for i, item in enumerate(self.items):
            row = i // self.cols
            col = i % self.cols
            x = col * (card_w + 6)
            y = self.height - (row + 1) * (self.card_height + 6) + 2

            # Card background
            self.canv.setFillColor(_hex_to_rl_color(p.neutral_light))
            self.canv.setStrokeColor(_hex_to_rl_color(p.neutral_mid))
            self.canv.setLineWidth(0.5)
            self.canv.roundRect(x, y, card_w, self.card_height, 4, fill=1, stroke=1)

            # Accent top bar
            trend_color = p.semantic.get("positive") if item.get("trend") == "up" else \
                          p.semantic.get("negative") if item.get("trend") == "down" else \
                          p.neutral_mid
            self.canv.setFillColor(_hex_to_rl_color(trend_color))
            self.canv.roundRect(x + 1, y + self.card_height - 4, card_w - 2, 4, 2, fill=1, stroke=0)

            # Label
            self.canv.setFillColor(_hex_to_rl_color(p.neutral_mid))
            self.canv.setFont(t.body_font, 7)
            self.canv.drawString(x + self.card_padding, y + self.card_height - 18,
                                 item.get("label", "").upper())

            # Value
            self.canv.setFillColor(_hex_to_rl_color(p.neutral_dark))
            self.canv.setFont(t.heading_font, 18)
            value_text = item.get("value", "")
            self.canv.drawString(x + self.card_padding, y + self.card_height - 40, value_text)

            # Change indicator
            change = item.get("change", "")
            if change:
                self.canv.setFont(t.body_font, 8)
                self.canv.setFillColor(_hex_to_rl_color(trend_color))
                self.canv.drawString(x + self.card_padding, y + 8, str(change))


# ── Flowable: CalloutBox ──────────────────────────────────────────────

class CalloutBox(Flowable):
    """An emphasized callout box with accent left border."""
    def __init__(self, text: str, theme: Theme, icon: str = ""):
        Flowable.__init__(self)
        self.text = text
        self.theme = theme
        self.icon = icon
        self.padding = 10

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        # Estimate text height
        t = self.theme.typography
        chars_per_line = max(1, int((availWidth - self.padding * 2 - 6) / (t.body_size * 0.5)))
        lines = (len(self.text) + chars_per_line - 1) // chars_per_line
        self.height = max(30, lines * t.body_size * 1.4 + self.padding * 2)
        return (availWidth, self.height)

    def draw(self):
        p = self.theme.palette
        t = self.theme.typography

        # Background
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_light))
        self.canv.setStrokeColor(_hex_to_rl_color(p.accent))
        self.canv.setLineWidth(3)
        self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        # Accent left bar
        self.canv.setFillColor(_hex_to_rl_color(p.accent))
        self.canv.rect(0, 0, 4, self.height, fill=1, stroke=0)

        # Text (simple line-wrapped)
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_dark))
        self.canv.setFont(t.body_font, t.body_size - 0.5)
        chars_per_line = max(1, int((self.width - self.padding * 2 - 10) / ((t.body_size - 0.5) * 0.48)))
        words = self.text.split()
        lines = []
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            if len(test) <= chars_per_line:
                current = test
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)

        y = self.height - self.padding - 2
        for line in lines:
            self.canv.drawString(self.padding + 6, y, line)
            y -= (t.body_size - 0.5) * 1.4


# ── Flowable: KeyFindingsBox ──────────────────────────────────────────

class KeyFindingsBox(Flowable):
    """A bordered box listing key findings."""
    def __init__(self, findings: list[str], theme: Theme):
        Flowable.__init__(self)
        self.findings = findings
        self.theme = theme
        self.padding = 12

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        t = self.theme.typography
        line_height = t.body_size * 1.5
        total_lines = 0
        chars_per_line = max(1, int((availWidth - self.padding * 2 - 20) / (t.body_size * 0.5)))
        for finding in self.findings:
            lines = (len(finding) + chars_per_line - 1) // chars_per_line
            total_lines += max(1, lines)
        self.height = total_lines * line_height + self.padding * 2 + 20  # + label
        return (availWidth, self.height)

    def draw(self):
        p = self.theme.palette
        t = self.theme.typography

        # Background box
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_light))
        self.canv.setStrokeColor(_hex_to_rl_color(p.primary))
        self.canv.setLineWidth(1)
        self.canv.roundRect(0, 0, self.width, self.height, 4, fill=1, stroke=1)

        # Label
        self.canv.setFillColor(_hex_to_rl_color(p.primary))
        self.canv.setFont(t.heading_font, 9)
        self.canv.drawString(self.padding, self.height - self.padding - 10, "KEY FINDINGS")

        # Findings
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_dark))
        chars_per_line = max(1, int((self.width - self.padding * 2 - 20) / (t.body_size * 0.48)))
        y = self.height - self.padding - 28
        line_height = t.body_size * 1.5

        for i, finding in enumerate(self.findings):
            # Bullet
            self.canv.setFont(t.heading_font, 10)
            self.canv.drawString(self.padding, y, "•")
            self.canv.setFont(t.body_font, t.body_size - 0.5)

            words = finding.split()
            lines = []
            current = ""
            for word in words:
                test = f"{current} {word}".strip()
                if len(test) <= chars_per_line:
                    current = test
                else:
                    lines.append(current)
                    current = word
            if current:
                lines.append(current)

            for line in lines:
                self.canv.drawString(self.padding + 14, y, line)
                y -= line_height
            y -= 2  # gap between findings


# ── Flowable: CaseStudy ───────────────────────────────────────────────

class CaseStudyBlock(Flowable):
    """A case study panel with company, challenge, solution, results."""
    def __init__(self, data: dict, theme: Theme):
        Flowable.__init__(self)
        self.data = data
        self.theme = theme
        self.padding = 12

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        t = self.theme.typography
        text = (self.data.get("challenge", "") + " " +
                self.data.get("solution", "") + " " +
                self.data.get("results", ""))
        chars_per_line = max(1, int((availWidth - self.padding * 2) / (t.body_size * 0.5)))
        lines = (len(text) + chars_per_line - 1) // chars_per_line
        self.height = lines * t.body_size * 1.5 + 60
        return (availWidth, self.height)

    def draw(self):
        p = self.theme.palette
        t = self.theme.typography

        # Card
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_light))
        self.canv.setStrokeColor(_hex_to_rl_color(p.secondary))
        self.canv.setLineWidth(1.5)
        self.canv.roundRect(0, 0, self.width, self.height, 6, fill=1, stroke=1)

        # Company header
        self.canv.setFillColor(_hex_to_rl_color(p.primary))
        self.canv.setFont(t.heading_font, t.heading_size_h3)
        company = self.data.get("company", "Case Study")
        self.canv.drawString(self.padding, self.height - 20, f"CASE STUDY: {company}")

        # Labels
        self.canv.setFont(t.body_font, t.body_size - 1)
        sections = [
            ("Challenge:", self.data.get("challenge", "")),
            ("Solution:", self.data.get("solution", "")),
            ("Results:", self.data.get("results", "")),
        ]
        y = self.height - 40
        for label, content in sections:
            if not content:
                continue
            self.canv.setFillColor(_hex_to_rl_color(p.secondary))
            self.canv.setFont(t.body_font, t.body_size - 0.5)
            self.canv.drawString(self.padding, y, label)
            self.canv.setFillColor(_hex_to_rl_color(p.neutral_dark))
            chars_per_line = max(1, int((self.width - self.padding * 2 - 70) / ((t.body_size - 0.5) * 0.48)))
            words = content.split()
            lines = []
            current = ""
            for word in words:
                test = f"{current} {word}".strip()
                if len(test) <= chars_per_line:
                    current = test
                else:
                    lines.append(current)
                    current = word
            if current:
                lines.append(current)
            for line in lines:
                self.canv.drawString(self.padding + 62, y, line)
                y -= (t.body_size - 0.5) * 1.5
            y -= 4


# ── Flowable: SWOTMatrix ──────────────────────────────────────────────

class SWOTMatrix(Flowable):
    """A 2×2 SWOT analysis matrix."""
    def __init__(self, swot_data: dict, theme: Theme):
        Flowable.__init__(self)
        self.swot = swot_data
        self.theme = theme
        self.padding = 8
        self.cell_padding = 6

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        self.cell_w = (availWidth - self.padding) / 2
        # Estimate height from longest list
        t = self.theme.typography
        max_items = max(
            len(self.swot.get("strengths", [])),
            len(self.swot.get("weaknesses", [])),
            len(self.swot.get("opportunities", [])),
            len(self.swot.get("threats", [])),
        )
        self.height = max_items * t.body_size * 1.5 + 40
        return (availWidth, self.height)

    def draw(self):
        p = self.theme.palette
        t = self.theme.typography
        h = self.height / 2
        cw = self.cell_w
        cp = self.cell_padding

        quadrants = [
            ("STRENGTHS", self.swot.get("strengths", []), 0, h, p.semantic["positive"]),
            ("WEAKNESSES", self.swot.get("weaknesses", []), cw + self.padding / 2, h, p.semantic["negative"]),
            ("OPPORTUNITIES", self.swot.get("opportunities", []), 0, 0, p.chart_colors[1]),
            ("THREATS", self.swot.get("threats", []), cw + self.padding / 2, 0, p.semantic["warning"]),
        ]

        line_height = t.body_size * 1.5

        for title, items, x, y, accent_color in quadrants:
            # Cell background
            self.canv.setFillColor(_hex_to_rl_color(p.neutral_light))
            self.canv.setStrokeColor(_hex_to_rl_color(p.neutral_mid))
            self.canv.setLineWidth(0.5)
            self.canv.rect(x, y, cw, h, fill=1, stroke=1)

            # Title bar
            self.canv.setFillColor(_hex_to_rl_color(accent_color))
            self.canv.rect(x, y + h - 16, cw, 16, fill=1, stroke=0)
            self.canv.setFillColor(colors.white)
            self.canv.setFont(t.heading_font, 9)
            self.canv.drawString(x + cp, y + h - 13, title)

            # Items
            self.canv.setFillColor(_hex_to_rl_color(p.neutral_dark))
            self.canv.setFont(t.body_font, t.body_size - 1)
            item_y = y + h - 30
            for item in items:
                self.canv.drawString(x + cp + 4, item_y, f"• {item[:80]}")
                item_y -= line_height


# ── Styled table builder ──────────────────────────────────────────────

def styled_table(headers: list[str], rows: list[list[str]],
                 theme: Theme, title: str = "",
                 col_widths: list[float] | None = None) -> list[Flowable]:
    """Build a styled data table as a list of flowables."""
    p = theme.palette
    t = theme.typography

    elements = []
    if title:
        elements.append(Paragraph(title, heading_style(theme, 3)))
        elements.append(Spacer(1, 4))

    # Build table data with header
    table_data = [headers] + rows

    # Styles
    header_color = _hex_to_rl_color(p.primary)
    row_even = _hex_to_rl_color(p.neutral_light)
    text_color = _hex_to_rl_color(p.neutral_dark)

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), header_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), t.body_font),
        ("FONTSIZE", (0, 0), (-1, 0), t.body_size - 1),
        ("FONTNAME", (0, 1), (-1, -1), t.body_font),
        ("FONTSIZE", (0, 1), (-1, -1), t.body_size - 1),
        ("TEXTCOLOR", (0, 1), (-1, -1), text_color),
        ("ALIGN", (0, 0), (-1, 0), "LEFT"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 1), (0, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, _hex_to_rl_color(p.neutral_mid)),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, row_even]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    tbl.setStyle(TableStyle(style_cmds))
    elements.append(tbl)

    return elements


# ── Chart image flowable ──────────────────────────────────────────────

def chart_image(buf: BytesIO, theme: Theme, caption: str = "",
                width_pt: float | None = None) -> list[Flowable]:
    """Create a chart image flowable from a BytesIO buffer."""
    elements = []

    # Determine image width
    if width_pt is None:
        width_pt = 450  # default

    img = Image(buf, width=width_pt, height=width_pt / 2.0)
    elements.append(img)

    if caption:
        elements.append(Paragraph(caption, caption_style(theme)))

    return elements


# ── Page spacer / filler ──────────────────────────────────────────────

class PageFiller(Spacer):
    """A spacer that can expand to fill remaining page space."""
    pass
