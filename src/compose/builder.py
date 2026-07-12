"""Report composition engine — builds complete ReportLab PDF from spec + theme.

Orchestrates: cover → TOC → executive summary → chapters → appendices → disclaimers.
Manages page templates, headers/footers, and content flow.
"""

import io
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import mm, inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, NextPageTemplate, PageBreak,
    Paragraph, Spacer, Image, Table, TableStyle, KeepTogether,
)
from reportlab.platypus.doctemplate import PageTemplate
from reportlab.platypus.frames import Frame
from reportlab.platypus.flowables import HRFlowable

from ..design.theme import Theme
from ..data.world_bank import WorldBankAPI
from ..charts.engine import (
    line_chart, bar_chart, grouped_bar_chart, stacked_area_chart,
    scatter_chart, waterfall_chart, donut_chart, heatmap_chart,
    radar_chart, slope_chart,
)
from .flowables import (
    _hex_to_rl_color, body_style, heading_style, caption_style,
    SectionDivider, KPICards, CalloutBox, KeyFindingsBox,
    CaseStudyBlock, SWOTMatrix, styled_table, chart_image,
)
from .cover import CoverPage


class ReportBuilder:
    """Assembles a complete market research report as a ReportLab PDF."""

    def __init__(self, spec: dict, theme: Theme | None = None,
                 use_brand: bool = True, data_cache_dir: str = "./cache"):
        self.spec = spec
        self.meta = spec["meta"]

        # Apply brand if requested
        if use_brand:
            from ..design.brand import apply_brand, generate_brand_theme
            if theme:
                self.theme = apply_brand(theme)
            else:
                # Generate a unique brand theme from the spec seed
                seed = self.meta.get("seed")
                if seed is None:
                    import random
                    seed = random.randint(0, 2**31 - 1)
                self.theme = generate_brand_theme(seed=seed)
        else:
            from ..design.brand import generate_brand_theme
            if theme:
                self.theme = theme
            else:
                seed = self.meta.get("seed")
                if seed is None:
                    import random
                    seed = random.randint(0, 2**31 - 1)
                self.theme = generate_brand_theme(seed=seed)

        self.wb = WorldBankAPI()
        self.story: list = []  # The flowable sequence
        self.chapter_num = 0
        self.figure_num = 0
        self.table_num = 0

        # Page setup
        page_size_name = self.meta.get("pages", {}).get("size", "A4")
        self.page_w, self.page_h = A4 if page_size_name == "A4" else letter

    def build(self) -> io.BytesIO:
        """Build the complete report and return a PDF BytesIO buffer.

        Returns:
            BytesIO buffer containing the PDF.
        """
        # Build the story (sequence of flowables)
        self._build_story()

        # Create document
        buf = io.BytesIO()
        doc = BaseDocTemplate(
            buf,
            pagesize=(self.page_w, self.page_h),
            leftMargin=self.theme.layout.margin_left,
            rightMargin=self.theme.layout.margin_right,
            topMargin=self.theme.layout.margin_top,
            bottomMargin=self.theme.layout.margin_bottom,
            title=self.meta.get("title", "Market Research Report"),
            author=self.meta.get("author", "H Heuristics Research"),
        )

        # Add page templates
        self._add_page_templates(doc)

        # Build PDF
        doc.build(self.story)
        buf.seek(0)
        return buf

    def build_to_file(self, output_path: str) -> Path:
        """Build the report and save to a file."""
        buf = self.build()
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(buf.read())
        return output_path

    # ── Page templates ──────────────────────────────────────────────

    def _add_page_templates(self, doc: BaseDocTemplate):
        """Add page templates with headers and footers."""
        p = self.theme.palette
        t = self.theme.typography
        pw = self.page_w
        ph = self.page_h
        ml = self.theme.layout.margin_left
        mr = self.theme.layout.margin_right
        mt = self.theme.layout.margin_top
        mb = self.theme.layout.margin_bottom

        # Content frame
        content_frame = Frame(ml, mb, pw - ml - mr, ph - mt - mb, id="content")

        def on_page(canvas, doc):
            """Draw header and footer on each page."""
            # Header line
            canvas.saveState()
            canvas.setStrokeColor(_hex_to_rl_color(p.neutral_mid))
            canvas.setLineWidth(0.5)
            canvas.line(ml, ph - mt + 8, pw - mr, ph - mt + 8)

            # Header text
            canvas.setFont(t.body_font, 7)
            canvas.setFillColor(_hex_to_rl_color(p.neutral_mid))
            title_short = self.meta.get("title", "")[:60]
            canvas.drawString(ml, ph - mt + 12, title_short)
            canvas.drawRightString(pw - mr, ph - mt + 12,
                                    self.meta.get("brand", "H Heuristics"))

            # Footer
            canvas.setFont(t.body_font, 7)
            canvas.drawCentredString(pw / 2, mb - 12,
                                      f"Page {canvas.getPageNumber()}")

            canvas.restoreState()

        def on_cover_page(canvas, doc):
            pass  # No headers/footers on cover

        # Normal page template
        normal_template = PageTemplate(
            id="normal", frames=[content_frame],
            onPage=on_page, pagesize=(pw, ph),
        )

        # Cover page template (no headers/footers)
        cover_frame = Frame(0, 0, pw, ph, id="cover")
        cover_template = PageTemplate(
            id="cover", frames=[cover_frame],
            onPage=on_cover_page, pagesize=(pw, ph),
        )

        doc.addPageTemplates([cover_template, normal_template])

    # ── Story builder ──────────────────────────────────────────────

    def _build_story(self):
        """Build the complete story from spec sections."""
        sections = self.spec.get("sections", [])

        for sec in sections:
            elements = self._render_section(sec)
            if elements:
                self.story.extend(elements)

    def _render_section(self, sec: dict) -> list:
        """Render a single section to a list of flowables."""
        stype = sec.get("type", "section")

        handlers = {
            "cover": self._render_cover,
            "toc": self._render_toc,
            "executive_summary": self._render_exec_summary,
            "chapter": self._render_chapter,
            "section": self._render_section_block,
            "subsection": self._render_subsection,
            "chart": self._render_chart_block,
            "table": self._render_table_block,
            "callout": self._render_callout,
            "key_findings": self._render_key_findings,
            "kpi_cards": self._render_kpi_cards,
            "case_study": self._render_case_study,
            "swot": self._render_swot,
            "market_sizing": self._render_market_sizing,
            "forecast": self._render_forecast,
            "competitive_matrix": self._render_competitive_matrix,
            "methodology": self._render_methodology,
            "timeline": self._render_timeline,
            "appendix": self._render_appendix,
            "references": self._render_references,
            "page_break": self._render_page_break,
            "disclaimer_page": self._render_disclaimer,
            "copyright_page": self._render_copyright,
        }

        handler = handlers.get(stype, self._render_generic)
        return handler(sec)

    # ── Cover ──────────────────────────────────────────────────────

    def _render_cover(self, sec: dict) -> list:
        """Render cover page."""
        cover = CoverPage(self.meta, self.theme, self.page_w, self.page_h)
        return [NextPageTemplate("cover"), cover, NextPageTemplate("normal"), PageBreak()]

    # ── TOC ─────────────────────────────────────────────────────────

    def _render_toc(self, sec: dict) -> list:
        """Render table of contents."""
        elements = []
        elements.append(Paragraph("Contents", heading_style(self.theme, 1)))
        elements.append(SectionDivider(self.theme))
        elements.append(Spacer(1, 12))

        # List chapters and sections
        sections = self.spec.get("sections", [])
        for s in sections:
            title = s.get("title", "")
            stype = s.get("type", "")

            if stype in ("cover", "toc", "page_break", "callout", "chart", "table",
                         "kpi_cards", "case_study", "swot", "disclaimer_page", "copyright_page"):
                continue

            if title:
                if stype == "chapter":
                    self.chapter_num += 1
                    prefix = f"{self.chapter_num}."
                    elements.append(Paragraph(
                        f"<b>{prefix} {title}</b>",
                        body_style(self.theme, size=11, bold=True, align=TA_LEFT)
                    ))
                elif stype == "executive_summary":
                    elements.append(Paragraph(
                        f"<b>{title}</b>",
                        body_style(self.theme, size=11, bold=True, align=TA_LEFT)
                    ))
                elif stype in ("appendix", "references", "methodology"):
                    elements.append(Paragraph(
                        f"<b>{title}</b>",
                        body_style(self.theme, size=10, bold=True, align=TA_LEFT)
                    ))
                else:
                    # Sub-items under chapters
                    prefix = f"{self.chapter_num}." if self.chapter_num else ""
                    elements.append(Paragraph(
                        f"&nbsp;&nbsp;&nbsp;{title}",
                        body_style(self.theme, size=9.5, align=TA_LEFT)
                    ))

        elements.append(PageBreak())
        return elements

    # ── Executive Summary ──────────────────────────────────────────

    def _render_exec_summary(self, sec: dict) -> list:
        """Render executive summary."""
        elements = []
        elements.append(Paragraph("Executive Summary", heading_style(self.theme, 1)))
        elements.append(SectionDivider(self.theme))
        elements.append(Spacer(1, 6))

        content = sec.get("content", "")
        if content:
            for para in content.split("\n\n"):
                para = para.strip()
                if para:
                    # First paragraph is lead
                    if para == content.split("\n\n")[0].strip():
                        elements.append(Paragraph(
                            para.replace("\n", "<br/>"),
                            body_style(self.theme, size=11, leading=16)
                        ))
                    else:
                        elements.append(Paragraph(
                            para.replace("\n", "<br/>"),
                            body_style(self.theme)
                        ))

        # KPI summary if included
        kpi_items = sec.get("kpi_items", [])
        if kpi_items:
            elements.append(Spacer(1, 10))
            elements.append(KeepTogether(KPICards(kpi_items, self.theme, cols=min(len(kpi_items), 4))))

        # NO trailing page break — next chapter's leading break handles it
        return elements

    # ── Chapter ────────────────────────────────────────────────────

    def _render_chapter(self, sec: dict) -> list:
        """Render a chapter with title and content. Page break BEFORE heading."""
        elements = []
        # Page break before each chapter ensures clean start without trailing blanks
        elements.append(PageBreak())
        title = sec.get("title", "")

        if title:
            elements.append(Paragraph(title, heading_style(self.theme, 1)))
            elements.append(SectionDivider(self.theme))
            elements.append(Spacer(1, 6))

        # Chapter content
        content = sec.get("content", "")
        if content:
            for para in content.split("\n\n"):
                para = para.strip()
                if para:
                    elements.append(Paragraph(para.replace("\n", "<br/>"), body_style(self.theme)))

        elements.append(Spacer(1, 8))

        # Subsections
        for sub in sec.get("subsections", []):
            sub_els = self._render_section(sub)
            if sub_els:
                elements.extend(sub_els)

        # NO trailing page break — next chapter's leading PageBreak handles it
        return elements

    # ── Section / Subsection ───────────────────────────────────────

    def _render_section_block(self, sec: dict) -> list:
        """Render a section heading and body."""
        elements = []
        title = sec.get("title", "")
        if title:
            elements.append(Paragraph(title, heading_style(self.theme, 2)))

        content = sec.get("content", "")
        if content:
            for para in content.split("\n\n"):
                para = para.strip()
                if para:
                    elements.append(Paragraph(para.replace("\n", "<br/>"), body_style(self.theme)))

        for sub in sec.get("subsections", []):
            sub_els = self._render_section(sub)
            if sub_els:
                elements.extend(sub_els)

        return elements

    def _render_subsection(self, sec: dict) -> list:
        """Render a subsection."""
        elements = []
        title = sec.get("title", "")
        if title:
            elements.append(Paragraph(title, heading_style(self.theme, 3)))

        content = sec.get("content", "")
        if content:
            for para in content.split("\n\n"):
                para = para.strip()
                if para:
                    elements.append(Paragraph(para.replace("\n", "<br/>"), body_style(self.theme)))

        return elements

    # ── Chart ──────────────────────────────────────────────────────

    def _render_chart_block(self, sec: dict) -> list:
        """Fetch data and render a chart."""
        ds = sec.get("data_source", {})
        chart_type = sec.get("chart_type", "line")
        chart_title = sec.get("chart_title", sec.get("title", ""))
        provider = ds.get("provider", "static")

        chart_buf = None
        fig_width = self.theme.layout.content_width * 0.95

        try:
            if provider == "world_bank":
                indicator = ds.get("indicator", "NY.GDP.MKTP.CD")
                countries = ds.get("countries", ["USA", "CHN", "JPN", "DEU", "GBR"])
                dr = ds.get("date_range", {})
                date_range = (dr.get("start", 2000), dr.get("end", 2023)) if dr else None

                result = self.wb.get_indicator_safe(indicator, countries, date_range)

                chart_data = {}
                for code, points in result.items():
                    if code == "_meta":
                        if not chart_title:
                            chart_title = result["_meta"].get("label", indicator)
                        continue
                    if points:
                        label = points[0].get("country", code)
                        chart_data[label] = points

                if chart_data:
                    if chart_type == "line":
                        chart_buf = line_chart(chart_data, self.theme, width_pt=fig_width,
                                                title=chart_title)
                    elif chart_type in ("bar", "horizontal_bar"):
                        chart_buf = bar_chart(chart_data, self.theme, width_pt=fig_width,
                                              title=chart_title,
                                              horizontal=(chart_type == "horizontal_bar"))
                    elif chart_type in ("area", "stacked_area"):
                        chart_buf = stacked_area_chart(chart_data, self.theme, width_pt=fig_width,
                                                       title=chart_title)

            elif provider == "static":
                td = sec.get("table_data", {})
                headers = td.get("headers", [])
                rows = td.get("rows", [])
                if headers and rows:
                    labels = [r[0] for r in rows if r]
                    values = []
                    for r in rows:
                        if len(r) > 1:
                            try:
                                values.append(float(r[1].replace(",", "").replace("%", "").strip()))
                            except (ValueError, IndexError):
                                values.append(0)
                    if labels and values:
                        chart_data = dict(zip(labels, values))
                        if chart_type in ("bar",):
                            chart_buf = bar_chart(chart_data, self.theme, width_pt=fig_width,
                                                  title=chart_title, horizontal=False)
                        elif chart_type == "horizontal_bar":
                            chart_buf = bar_chart(chart_data, self.theme, width_pt=fig_width,
                                                  title=chart_title, horizontal=True)
                        elif chart_type == "donut":
                            chart_buf = donut_chart(chart_data, self.theme, width_pt=fig_width * 0.7,
                                                    title=chart_title)
        except Exception as e:
            print(f"  [WARN] Chart '{chart_title}' failed: {e}")

        elements = []
        if chart_buf:
            self.figure_num += 1
            caption = f"Figure {self.figure_num}: {chart_title}"
            elements.extend(chart_image(chart_buf, self.theme, caption=caption,
                                        width_pt=fig_width))
        else:
            elements.append(Paragraph(
                f"<i>[Chart: {chart_title} — data unavailable]</i>",
                body_style(self.theme, align=TA_CENTER)
            ))

        elements.append(Spacer(1, 6))
        return [KeepTogether(elements)]

    # ── Table ──────────────────────────────────────────────────────

    def _render_table_block(self, sec: dict) -> list:
        """Render a data table."""
        td = sec.get("table_data", {})
        headers = td.get("headers", [])
        rows = td.get("rows", [])
        table_title = sec.get("title", "")

        if not headers or not rows:
            return []

        self.table_num += 1
        full_title = f"Table {self.table_num}: {table_title}" if table_title else ""
        return [KeepTogether(styled_table(headers, rows, self.theme, title=full_title))]

    # ── Callout / Key Findings / KPI Cards ─────────────────────────

    def _render_callout(self, sec: dict) -> list:
        text = sec.get("content", "")
        if not text:
            return []
        return [KeepTogether(CalloutBox(text, self.theme)), Spacer(1, 6)]

    def _render_key_findings(self, sec: dict) -> list:
        content = sec.get("content", "")
        if not content:
            return []
        findings = [f.strip() for f in content.split("\n") if f.strip()]
        if not findings:
            findings = [content]
        return [KeepTogether(KeyFindingsBox(findings, self.theme)), Spacer(1, 8)]

    def _render_kpi_cards(self, sec: dict) -> list:
        kpi_items = sec.get("kpi_items", [])
        if not kpi_items:
            return []
        cols = sec.get("columns", min(len(kpi_items), 4))
        return [KeepTogether(KPICards(kpi_items, self.theme, cols=cols)), Spacer(1, 6)]

    # ── Case Study / SWOT ─────────────────────────────────────────

    def _render_case_study(self, sec: dict) -> list:
        data = sec.get("case_study_data", {})
        if not data:
            return []
        return [KeepTogether(CaseStudyBlock(data, self.theme)), Spacer(1, 8)]

    def _render_swot(self, sec: dict) -> list:
        swot = sec.get("swot_data", {})
        if not swot:
            return []
        elements = []
        title = sec.get("title", "SWOT Analysis")
        if title:
            elements.append(Paragraph(title, heading_style(self.theme, 2)))
            elements.append(Spacer(1, 4))
        return [KeepTogether(SWOTMatrix(swot, self.theme)), Spacer(1, 8)]

    # ── Special report sections ────────────────────────────────────

    def _render_market_sizing(self, sec: dict) -> list:
        """Render a market sizing section with TAM/SAM/SOM estimates."""
        elements = []
        title = sec.get("title", "Market Sizing & Opportunity Assessment")
        elements.append(Paragraph(title, heading_style(self.theme, 2)))

        content = sec.get("content", "")
        if content:
            for para in content.split("\n\n"):
                para = para.strip()
                if para:
                    elements.append(Paragraph(para.replace("\n", "<br/>"), body_style(self.theme)))

        # KPI cards for TAM/SAM/SOM
        kpi = sec.get("kpi_items", [])
        if kpi:
            elements.append(Spacer(1, 8))
            elements.append(KPICards(kpi, self.theme, cols=min(len(kpi), 3)))
            elements.append(Spacer(1, 6))

        return elements

    def _render_forecast(self, sec: dict) -> list:
        """Render a forecast/outlook section."""
        elements = []
        title = sec.get("title", "Forecast & Future Outlook")
        elements.append(Paragraph(title, heading_style(self.theme, 2)))

        content = sec.get("content", "")
        if content:
            for para in content.split("\n\n"):
                para = para.strip()
                if para:
                    elements.append(Paragraph(para.replace("\n", "<br/>"), body_style(self.theme)))

        for sub in sec.get("subsections", []):
            sub_els = self._render_section(sub)
            if sub_els:
                elements.extend(sub_els)

        return elements

    def _render_competitive_matrix(self, sec: dict) -> list:
        """Render competitive landscape matrix."""
        elements = []
        title = sec.get("title", "Competitive Landscape")
        elements.append(Paragraph(title, heading_style(self.theme, 2)))

        content = sec.get("content", "")
        if content:
            for para in content.split("\n\n"):
                para = para.strip()
                if para:
                    elements.append(Paragraph(para.replace("\n", "<br/>"), body_style(self.theme)))

        # Competitive matrix table
        td = sec.get("table_data", {})
        if td:
            headers = td.get("headers", [])
            rows = td.get("rows", [])
            if headers and rows:
                self.table_num += 1
                elements.extend(styled_table(
                    headers, rows, self.theme,
                    title=f"Table {self.table_num}: Competitive Positioning"
                ))

        return elements

    def _render_methodology(self, sec: dict) -> list:
        """Render methodology section. Page break before heading."""
        elements = []
        elements.append(PageBreak())
        title = sec.get("title", "Methodology & Data Sources")
        elements.append(Paragraph(title, heading_style(self.theme, 1)))
        elements.append(SectionDivider(self.theme))
        elements.append(Spacer(1, 6))

        content = sec.get("content", "")
        if content:
            for para in content.split("\n\n"):
                para = para.strip()
                if para:
                    elements.append(Paragraph(para.replace("\n", "<br/>"), body_style(self.theme)))

        # NO trailing page break — next section's leading PageBreak handles it
        return elements

    def _render_timeline(self, sec: dict) -> list:
        """Render a timeline section."""
        elements = []
        title = sec.get("title", "Key Milestones & Timeline")
        elements.append(Paragraph(title, heading_style(self.theme, 2)))

        content = sec.get("content", "")
        if content:
            for para in content.split("\n\n"):
                para = para.strip()
                if para:
                    elements.append(Paragraph(para.replace("\n", "<br/>"), body_style(self.theme)))

        return elements

    def _render_appendix(self, sec: dict) -> list:
        """Render appendix."""
        elements = []
        title = sec.get("title", "Appendix")
        elements.append(Paragraph(title, heading_style(self.theme, 1)))
        elements.append(SectionDivider(self.theme))
        elements.append(Spacer(1, 8))

        content = sec.get("content", "")
        if content:
            for para in content.split("\n\n"):
                para = para.strip()
                if para:
                    elements.append(Paragraph(
                        para.replace("\n", "<br/>"),
                        body_style(self.theme, size=8.5)
                    ))

        return elements

    def _render_references(self, sec: dict) -> list:
        """Render references."""
        elements = []
        title = sec.get("title", "References & Data Sources")
        elements.append(Paragraph(title, heading_style(self.theme, 1)))
        elements.append(SectionDivider(self.theme))
        elements.append(Spacer(1, 8))

        content = sec.get("content", "")
        if content:
            for para in content.split("\n\n"):
                para = para.strip()
                if para:
                    elements.append(Paragraph(
                        para.replace("\n", "<br/>"),
                        body_style(self.theme, size=8)
                    ))

        # Default data provenance
        elements.append(Spacer(1, 12))
        provenance = [
            "Data Sources: World Bank Data API, FRED (Federal Reserve Economic Data), "
            "industry reports, and curated market intelligence datasets.",
            f"Report Generated: {self.meta.get('date', 'N/A')}",
            f"Report ID: {self.meta.get('report_id', 'MRR-AUTO-001')}",
            "Classification: " + self.meta.get("classification", "Public"),
        ]
        for line in provenance:
            elements.append(Paragraph(line, body_style(self.theme, size=7.5)))

        return elements

    # ── Utility sections ───────────────────────────────────────────

    def _render_page_break(self, sec: dict) -> list:
        return [PageBreak()]

    def _render_disclaimer(self, sec: dict) -> list:
        """Render legal disclaimer page."""
        elements = []
        elements.append(Paragraph("Disclaimer & Legal Notice", heading_style(self.theme, 1)))
        elements.append(SectionDivider(self.theme))
        elements.append(Spacer(1, 12))

        disclaimer = sec.get("content", self.meta.get("disclaimer",
            "This report is published by H Heuristics for informational purposes only. "
            "It does not constitute investment, legal, or professional advice. "
            "While every effort has been made to ensure the accuracy of the information "
            "contained herein, H Heuristics makes no warranty, express or implied, "
            "as to the completeness or accuracy of the data, analysis, or conclusions. "
            "Market conditions, regulations, and industry dynamics are subject to change. "
            "Readers should conduct their own due diligence and consult qualified "
            "professionals before making business decisions based on this report.\n\n"
            "© H Heuristics. All rights reserved. No part of this publication may be "
            "reproduced, distributed, or transmitted in any form without the prior "
            "written permission of H Heuristics, except for brief quotations in "
            "reviews and certain non-commercial uses permitted by copyright law.\n\n"
            "H Heuristics is a trading name of H Heuristics Ltd, registered in England "
            "and Wales. Registered office: Suite 962, 37 Westminster Buildings, "
            "Theatre Square, Nottingham, NG1 6LG, United Kingdom."
        ))

        for para in disclaimer.split("\n\n"):
            para = para.strip()
            if para:
                elements.append(Paragraph(
                    para.replace("\n", "<br/>"),
                    body_style(self.theme, size=8.5)
                ))

        return elements

    def _render_copyright(self, sec: dict) -> list:
        """Render copyright page."""
        elements = []
        elements.append(Spacer(1, 40))
        p = self.theme.palette
        t = self.theme.typography
        center = TA_CENTER

        elements.append(Paragraph(
            self.meta.get("title", "Report Title"),
            ParagraphStyle("cp_title", fontName=t.heading_font, fontSize=16,
                           leading=20, textColor=_hex_to_rl_color(p.neutral_dark),
                           alignment=center, spaceAfter=20)
        ))
        elements.append(Paragraph(
            f"Published by {self.meta.get('brand', 'H Heuristics')}",
            ParagraphStyle("cp_pub", fontName=t.body_font, fontSize=10,
                           textColor=_hex_to_rl_color(p.neutral_mid), alignment=center)
        ))
        elements.append(Paragraph(
            self.meta.get("date", ""),
            ParagraphStyle("cp_date", fontName=t.body_font, fontSize=10,
                           textColor=_hex_to_rl_color(p.neutral_mid), alignment=center)
        ))
        elements.append(Spacer(1, 30))
        elements.append(Paragraph(
            "© H Heuristics. All Rights Reserved.",
            ParagraphStyle("cp_copy", fontName=t.body_font, fontSize=9,
                           textColor=_hex_to_rl_color(p.neutral_mid), alignment=center)
        ))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            "www.hheuristics.com",
            ParagraphStyle("cp_url", fontName=t.body_font, fontSize=9,
                           textColor=_hex_to_rl_color(p.accent), alignment=center)
        ))

        elements.append(PageBreak())
        return elements

    # ── Generic fallback ───────────────────────────────────────────

    def _render_generic(self, sec: dict) -> list:
        """Generic renderer for unrecognized section types."""
        elements = []
        title = sec.get("title", "")
        if title:
            elements.append(Paragraph(title, heading_style(self.theme, 2)))

        content = sec.get("content", "")
        if content:
            for para in content.split("\n\n"):
                para = para.strip()
                if para:
                    elements.append(Paragraph(para.replace("\n", "<br/>"), body_style(self.theme)))

        for sub in sec.get("subsections", []):
            sub_els = self._render_section(sub)
            if sub_els:
                elements.extend(sub_els)

        return elements
