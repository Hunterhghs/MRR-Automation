"""Custom ReportLab flowables for professional market research reports.

Includes: KPI cards, callout boxes, key findings panels, case study blocks,
SWOT matrices, timeline graphics, section dividers, and branded elements.

All text measurement uses canvas.stringWidth() for accurate proportional-font
wrapping — no more crude character-count estimates that cause text overlap.
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


# ── Shared text measurement utilities ──────────────────────────────────

def _wrap_text_to_lines(
    text: str, max_width: float, font_name: str, font_size: float
) -> list[str]:
    """Wrap text into lines using exact stringWidth measurement for proportional fonts.

    Args:
        text: The full text to wrap.
        max_width: Maximum line width in points.
        font_name: ReportLab-registered font name.
        font_size: Font size in points.

    Returns:
        List of line strings that each fit within max_width.
    """
    lines = []
    words = text.split()
    if not words:
        return [""]

    current_line = words[0]

    # Handle case where first word itself is too long
    if stringWidth(current_line, font_name, font_size) > max_width:
        lines.extend(_split_long_token(current_line, max_width, font_name, font_size))
        current_line = ""

    for word in words[1:]:
        test_line = f"{current_line} {word}" if current_line else word
        if stringWidth(test_line, font_name, font_size) <= max_width:
            current_line = test_line
        else:
            # Push current line and start new one
            if current_line:
                lines.append(current_line)
            # If the new word itself is too long, split by character
            if stringWidth(word, font_name, font_size) > max_width:
                lines.extend(_split_long_token(word, max_width, font_name, font_size))
                current_line = ""
            else:
                current_line = word
    if current_line:
        lines.append(current_line)
    return lines


def _split_long_token(
    token: str, max_width: float, font_name: str, font_size: float
) -> list[str]:
    """Split a single too-long token into chunks that fit within max_width."""
    result = []
    current = ""
    for ch in token:
        if stringWidth(current + ch, font_name, font_size) <= max_width:
            current += ch
        else:
            if current:
                result.append(current)
            current = ch
    if current:
        result.append(current)
    return result


def _measure_text_height(
    text: str, max_width: float, font_name: str, font_size: float, line_spacing: float
) -> tuple[int, float]:
    """Measure how many lines and total height text will occupy.

    Returns:
        Tuple of (line_count, total_height).
    """
    lines = _wrap_text_to_lines(text, max_width, font_name, font_size)
    return len(lines), len(lines) * line_spacing


# ── Base styled paragraph helpers ──────────────────────────────────────

def body_style(theme: Theme, size: int | None = None, bold: bool = False,
               align: int = TA_JUSTIFY, leading: float | None = None) -> ParagraphStyle:
    """Standard body paragraph style."""
    t = theme.typography
    sz = size or t.body_size
    ld = leading or (sz * 1.55)
    return ParagraphStyle(
        f"Body-{sz}", fontName=t.body_font, fontSize=sz,
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
        f"Heading{level}-{sz}", fontName=t.heading_font,
        fontSize=sz, leading=sz * 1.25,
        textColor=_hex_to_rl_color(color),
        spaceBefore=space_before, spaceAfter=space_after,
        pageBreakAfter=None if level >= 2 else None,  # prevent orphaned h2/h3
    )


def caption_style(theme: Theme) -> ParagraphStyle:
    """Figure/table caption style."""
    t = theme.typography
    p = theme.palette
    return ParagraphStyle(
        "Caption", fontName=t.body_font,
        fontSize=t.caption_size, leading=t.caption_size * 1.3,
        textColor=_hex_to_rl_color(p.neutral_mid),
        alignment=TA_CENTER, spaceAfter=4,
    )


# ── Flowable: SectionDivider ──────────────────────────────────────────

class SectionDivider(Flowable):
    """A horizontal rule divider between sections."""
    def __init__(self, theme: Theme, thickness: float = 1.5):
        Flowable.__init__(self)
        self.theme = theme
        self.thickness = thickness
        self.width = 0
        self.height = thickness + 10

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
    """A row of KPI metric cards (2-4 per row).

    Uses exact stringWidth measurement for labels and values to
    prevent text clipping within cards.
    """
    def __init__(self, kpi_items: list[dict], theme: Theme, cols: int = 3):
        Flowable.__init__(self)
        self.items = kpi_items
        self.theme = theme
        self.cols = min(cols, max(1, len(kpi_items)))
        self.card_padding = 10

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        self.card_w = (availWidth - (self.cols - 1) * 8) / self.cols
        # Dynamic card height based on content
        t = self.theme.typography
        # Label area (1 line @ 7pt) + value (1 line @ 18pt) + change (1 line @ 8pt) + padding
        self.card_height = 68
        rows = (len(self.items) + self.cols - 1) // self.cols
        self.height = rows * (self.card_height + 8) + 4
        return (availWidth, self.height)

    def draw(self):
        p = self.theme.palette
        t = self.theme.typography

        for i, item in enumerate(self.items):
            row = i // self.cols
            col = i % self.cols
            x = col * (self.card_w + 8)
            y = self.height - (row + 1) * (self.card_height + 8) + 4

            # Card background
            self.canv.setFillColor(_hex_to_rl_color(p.neutral_light))
            self.canv.setStrokeColor(_hex_to_rl_color(p.neutral_mid))
            self.canv.setLineWidth(0.5)
            self.canv.roundRect(x, y, self.card_w, self.card_height, 4, fill=1, stroke=1)

            # Accent top bar
            trend_color = p.semantic.get("positive") if item.get("trend") == "up" else \
                          p.semantic.get("negative") if item.get("trend") == "down" else \
                          p.neutral_mid
            self.canv.setFillColor(_hex_to_rl_color(trend_color))
            self.canv.roundRect(x + 2, y + self.card_height - 4, self.card_w - 4, 4, 2, fill=1, stroke=0)

            # Label — wrap to 2 lines if needed, truncate as last resort
            label = item.get("label", "").upper()
            label_font_size = 7
            max_label_w = self.card_w - self.card_padding * 2
            self.canv.setFont(t.body_font, label_font_size)
            self.canv.setFillColor(_hex_to_rl_color(p.neutral_mid))
            if stringWidth(label, t.body_font, label_font_size) <= max_label_w:
                self.canv.drawString(x + self.card_padding, y + self.card_height - 18, label)
            else:
                # Try wrapping to 2 lines
                label_lines = _wrap_text_to_lines(label, max_label_w, t.body_font, label_font_size)
                if len(label_lines) <= 2:
                    for li, ll in enumerate(label_lines):
                        ly = y + self.card_height - 18 - li * (label_font_size + 1)
                        self.canv.drawString(x + self.card_padding, ly, ll)
                else:
                    # Still too long — truncate line 2 with ellipsis
                    self.canv.drawString(x + self.card_padding, y + self.card_height - 18, label_lines[0])
                    trunc = label_lines[1]
                    while trunc and stringWidth(trunc + "...", t.body_font, label_font_size) > max_label_w:
                        trunc = trunc[:-1]
                    self.canv.drawString(x + self.card_padding, y + self.card_height - 18 - (label_font_size + 1), trunc + "...")

            # Value
            value_text = item.get("value", "")
            value_font_size = 18
            self.canv.setFont(t.heading_font, value_font_size)
            if stringWidth(value_text, t.heading_font, value_font_size) > max_label_w:
                value_font_size = 14
                self.canv.setFont(t.heading_font, value_font_size)
                if stringWidth(value_text, t.heading_font, value_font_size) > max_label_w:
                    value_font_size = 11
                    self.canv.setFont(t.heading_font, value_font_size)
            self.canv.setFillColor(_hex_to_rl_color(p.neutral_dark))
            self.canv.drawString(x + self.card_padding, y + self.card_height - 40, value_text)

            # Change indicator
            change = item.get("change", "")
            if change:
                change_font_size = 8
                self.canv.setFont(t.body_font, change_font_size)
                if stringWidth(str(change), t.body_font, change_font_size) > max_label_w:
                    change_font_size = 7
                    self.canv.setFont(t.body_font, change_font_size)
                self.canv.setFillColor(_hex_to_rl_color(trend_color))
                self.canv.drawString(x + self.card_padding, y + 8, str(change))


# ── Flowable: CalloutBox ──────────────────────────────────────────────

class CalloutBox(Flowable):
    """An emphasized callout box with accent left border.

    Uses exact stringWidth line-wrapping in both wrap() and draw().
    """
    def __init__(self, text: str, theme: Theme, icon: str = ""):
        Flowable.__init__(self)
        self.text = text
        self.theme = theme
        self.icon = icon
        self.padding = 12

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        t = self.theme.typography
        font_size = t.body_size - 0.5
        line_spacing = font_size * 1.55
        text_width = availWidth - self.padding * 2 - 12  # 12 for accent bar offset

        self._lines = _wrap_text_to_lines(self.text, text_width, t.body_font, font_size)

        self.height = max(30, len(self._lines) * line_spacing + self.padding * 2)
        return (availWidth, self.height)

    def draw(self):
        p = self.theme.palette
        t = self.theme.typography
        font_size = t.body_size - 0.5
        line_spacing = font_size * 1.55

        # Background
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_light))
        self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)

        # Accent left bar
        self.canv.setFillColor(_hex_to_rl_color(p.accent))
        self.canv.rect(0, 0, 4, self.height, fill=1, stroke=0)

        # Text — use the SAME lines computed in wrap()
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_dark))
        self.canv.setFont(t.body_font, font_size)

        y = self.height - self.padding - 2
        for line in self._lines:
            self.canv.drawString(self.padding + 8, y, line)
            y -= line_spacing


# ── Flowable: KeyFindingsBox ──────────────────────────────────────────

class KeyFindingsBox(Flowable):
    """A bordered box listing key findings.

    Uses exact stringWidth for line wrapping with identical wrap/draw logic.
    """
    def __init__(self, findings: list[str], theme: Theme):
        Flowable.__init__(self)
        self.findings = findings
        self.theme = theme
        self.padding = 12

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        t = self.theme.typography
        font_size = t.body_size - 0.5
        line_spacing = font_size * 1.55
        bullet_offset = 16
        text_width = availWidth - self.padding * 2 - bullet_offset

        self._finding_lines = []
        total_lines = 0
        for finding in self.findings:
            wrapped = _wrap_text_to_lines(finding, text_width, t.body_font, font_size)
            self._finding_lines.append(wrapped)
            total_lines += max(1, len(wrapped))

        self.height = total_lines * line_spacing + self.padding * 2 + 22  # + label
        return (availWidth, self.height)

    def draw(self):
        p = self.theme.palette
        t = self.theme.typography
        font_size = t.body_size - 0.5
        line_spacing = font_size * 1.55

        # Background box
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_light))
        self.canv.setStrokeColor(_hex_to_rl_color(p.primary))
        self.canv.setLineWidth(1)
        self.canv.roundRect(0, 0, self.width, self.height, 4, fill=1, stroke=1)

        # Label
        self.canv.setFillColor(_hex_to_rl_color(p.primary))
        self.canv.setFont(t.heading_font, 9)
        self.canv.drawString(self.padding, self.height - self.padding - 10, "KEY FINDINGS")

        # Findings — use SAME lines computed in wrap()
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_dark))
        y = self.height - self.padding - 28

        for wrapped in self._finding_lines:
            if not wrapped:
                continue
            self.canv.setFont(t.heading_font, 10)
            self.canv.drawString(self.padding, y + 2, "\u2022")  # bullet
            self.canv.setFont(t.body_font, font_size)
            for line in wrapped:
                self.canv.drawString(self.padding + 14, y, line)
                y -= line_spacing
            y -= 2  # gap between findings


# ── Flowable: CaseStudy ───────────────────────────────────────────────

class CaseStudyBlock(Flowable):
    """A case study panel with company, challenge, solution, results.

    Uses exact stringWidth for all text measurement.
    """
    def __init__(self, data: dict, theme: Theme):
        Flowable.__init__(self)
        self.data = data
        self.theme = theme
        self.padding = 12

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        t = self.theme.typography
        font_size = t.body_size - 0.5
        line_spacing = font_size * 1.55
        label_width = 65
        text_width = availWidth - self.padding * 2 - label_width - 4

        self._section_lines = {}
        total_lines = 0
        sections = [
            ("challenge", "Challenge:"),
            ("solution", "Solution:"),
            ("results", "Results:"),
        ]
        for key, label in sections:
            content = self.data.get(key, "")
            if content:
                wrapped = _wrap_text_to_lines(content, text_width, t.body_font, font_size)
                self._section_lines[key] = wrapped
                total_lines += len(wrapped)
                total_lines += 1  # for the label line

        self.height = total_lines * line_spacing + self.padding * 2 + 28  # + title
        return (availWidth, self.height)

    def draw(self):
        p = self.theme.palette
        t = self.theme.typography
        font_size = t.body_size - 0.5
        line_spacing = font_size * 1.55
        label_width = 65

        # Card background
        self.canv.setFillColor(_hex_to_rl_color(p.neutral_light))
        self.canv.setStrokeColor(_hex_to_rl_color(p.secondary))
        self.canv.setLineWidth(1.5)
        self.canv.roundRect(0, 0, self.width, self.height, 6, fill=1, stroke=1)

        # Company header — adaptive font sizing for long names
        self.canv.setFillColor(_hex_to_rl_color(p.primary))
        company = self.data.get("company", "Case Study")
        full_title = f"CASE STUDY: {company}"
        title_fs = t.heading_size_h3
        max_title_w = self.width - self.padding * 2
        while title_fs >= 7 and stringWidth(full_title, t.heading_font, title_fs) > max_title_w:
            title_fs -= 1
        self.canv.setFont(t.heading_font, title_fs)
        self.canv.drawString(self.padding, self.height - 20, full_title)

        # Section labels + content — use SAME lines computed in wrap()
        y = self.height - 40
        sections = [
            ("challenge", "Challenge:"),
            ("solution", "Solution:"),
            ("results", "Results:"),
        ]
        for key, label in sections:
            wrapped = self._section_lines.get(key)
            if not wrapped:
                continue
            self.canv.setFillColor(_hex_to_rl_color(p.secondary))
            self.canv.setFont(t.body_font, font_size)
            self.canv.drawString(self.padding, y, label)
            self.canv.setFillColor(_hex_to_rl_color(p.neutral_dark))
            for line in wrapped:
                self.canv.drawString(self.padding + label_width + 2, y, line)
                y -= line_spacing
            y -= 3  # gap between sections


# ── Flowable: SWOTMatrix ──────────────────────────────────────────────

class SWOTMatrix(Flowable):
    """A 2×2 SWOT analysis matrix.

    Uses exact stringWidth for item text to prevent overflow.
    Items are NOT hard-truncated; long items wrap within their quadrant.
    """
    def __init__(self, swot_data: dict, theme: Theme):
        Flowable.__init__(self)
        self.swot = swot_data
        self.theme = theme
        self.padding = 8
        self.cell_padding = 5

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        self.cell_w = (availWidth - self.padding) / 2
        t = self.theme.typography
        item_font_size = t.body_size - 1.5
        line_spacing = item_font_size * 1.2
        text_width_per_cell = self.cell_w - self.cell_padding * 2 - 6

        self._quadrant_lines = {}
        max_cell_lines = 0

        quad_keys = ["strengths", "weaknesses", "opportunities", "threats"]
        for key in quad_keys:
            items = self.swot.get(key, [])
            all_lines = []
            for item in items:
                wrapped = _wrap_text_to_lines(item, text_width_per_cell, t.body_font, item_font_size)
                all_lines.extend(wrapped)
            self._quadrant_lines[key] = all_lines
            max_cell_lines = max(max_cell_lines, len(all_lines))

        # Add 2 extra lines buffer for title bar
        self._cell_inner_h = (max_cell_lines + 0) * line_spacing + self.cell_padding * 2 + 18
        self.height = self._cell_inner_h * 2 + self.padding + 2
        return (availWidth, self.height)

    def draw(self):
        p = self.theme.palette
        t = self.theme.typography
        item_font_size = t.body_size - 1.5
        line_spacing = item_font_size * 1.25
        cw = self.cell_w
        cp = self.cell_padding
        cell_h = self._cell_inner_h
        h = cell_h  # each quadrant is half the total height

        quadrants = [
            ("STRENGTHS", self._quadrant_lines.get("strengths", []), 0, h, p.semantic["positive"]),
            ("WEAKNESSES", self._quadrant_lines.get("weaknesses", []), cw + self.padding, h, p.semantic["negative"]),
            ("OPPORTUNITIES", self._quadrant_lines.get("opportunities", []), 0, 0, p.chart_colors[1]),
            ("THREATS", self._quadrant_lines.get("threats", []), cw + self.padding, 0, p.semantic["warning"]),
        ]

        for title, lines, x, y, accent_color in quadrants:
            # Cell background
            self.canv.setFillColor(_hex_to_rl_color(p.neutral_light))
            self.canv.setStrokeColor(_hex_to_rl_color(p.neutral_mid))
            self.canv.setLineWidth(0.5)
            self.canv.rect(x, y, cw, h, fill=1, stroke=1)

            # Title bar
            title_bar_h = 22
            self.canv.setFillColor(_hex_to_rl_color(accent_color))
            self.canv.rect(x, y + h - title_bar_h, cw, title_bar_h, fill=1, stroke=0)
            self.canv.setFillColor(colors.white)
            self.canv.setFont(t.heading_font, 10)
            self.canv.drawString(x + cp, y + h - title_bar_h + 6, title)

            # Items — use SAME lines computed in wrap()
            self.canv.setFillColor(_hex_to_rl_color(p.neutral_dark))
            self.canv.setFont(t.body_font, item_font_size)
            item_y = y + h - title_bar_h - cp - 8
            for line in lines:
                self.canv.drawString(x + cp + 6, item_y, f"\u2022 {line}")
                item_y -= line_spacing


# ── Styled table builder ──────────────────────────────────────────────

def styled_table(headers: list[str], rows: list[list[str]],
                 theme: Theme, title: str = "",
                 col_widths: list[float] | None = None) -> list[Flowable]:
    """Build a styled data table with text-wrapping Paragraph cells.

    Unlike raw strings, Paragraph cells wrap text within column widths,
    preventing cell overflow and text overlap between columns.
    """
    p = theme.palette
    t = theme.typography

    elements = []
    if title:
        elements.append(Paragraph(title, heading_style(theme, 3)))
        elements.append(Spacer(1, 4))

    # Determine column widths if not provided — smart allocation
    if col_widths is None:
        n_cols = len(headers)
        # Use actual frame width (~464pt for A4 with 22mm margins)
        total_w = 460.0
        if n_cols <= 3:
            # For few columns: give extra width to first (label) column
            first_w = total_w * 0.40
            rest_w = (total_w - first_w) / (n_cols - 1) if n_cols > 1 else 0
            col_widths = [first_w] + [rest_w] * (n_cols - 1)
        elif n_cols <= 5:
            # For 4-5 columns: proportional allocation
            first_w = total_w * 0.30
            rest_w = (total_w - first_w) / (n_cols - 1)
            col_widths = [first_w] + [rest_w] * (n_cols - 1)
        else:
            # For 6+ columns: more even, but first column gets extra
            first_w = total_w * 0.22
            rest_w = (total_w - first_w) / (n_cols - 1)
            col_widths = [first_w] + [rest_w] * (n_cols - 1)

    # Cell paragraph styles
    header_style = ParagraphStyle(
        "TableHeader", fontName=t.body_font, fontSize=t.body_size - 1,
        leading=(t.body_size - 1) * 1.3, textColor=colors.white,
        alignment=TA_LEFT,
    )
    cell_style_left = ParagraphStyle(
        "TableCellLeft", fontName=t.body_font, fontSize=t.body_size - 2,
        leading=(t.body_size - 2) * 1.3, textColor=_hex_to_rl_color(p.neutral_dark),
        alignment=TA_LEFT,
    )
    cell_style_right = ParagraphStyle(
        "TableCellRight", fontName=t.body_font, fontSize=t.body_size - 2,
        leading=(t.body_size - 2) * 1.3, textColor=_hex_to_rl_color(p.neutral_dark),
        alignment=TA_RIGHT,
    )

    # Build table data with Paragraph-wrapped cells
    header_row = [Paragraph(h, header_style) for h in headers]
    data_rows = []
    for row in rows:
        para_row = []
        for i, cell in enumerate(row):
            style = cell_style_left if i == 0 else cell_style_right
            para_row.append(Paragraph(str(cell), style))
        data_rows.append(para_row)

    table_data = [header_row] + data_rows

    header_color = _hex_to_rl_color(p.primary)
    row_even = _hex_to_rl_color(p.neutral_light)

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), header_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, _hex_to_rl_color(p.neutral_mid)),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, row_even]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
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

    if width_pt is None:
        width_pt = 450

    img = Image(buf, width=width_pt, height=width_pt / 2.0)
    elements.append(img)

    if caption:
        elements.append(Paragraph(caption, caption_style(theme)))

    return elements


# ── Page spacer / filler ──────────────────────────────────────────────

class PageFiller(Spacer):
    """A spacer that can expand to fill remaining page space."""
    pass
