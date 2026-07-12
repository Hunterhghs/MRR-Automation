#!/usr/bin/env python3
"""MRR Automation — H Heuristics Market Research Report Generator.

Usage:
    mrr-automation generate spec.yaml [-o output.pdf] [--seed 42] [--no-brand]
    mrr-automation theme-preview [--seed 42]
    mrr-automation version
"""

import os
import sys
import random
from pathlib import Path

import click

from .spec.parser import load_spec, SpecError
from .design.theme import generate_theme
from .design.brand import H_HEURISTICS_THEME
from .compose.builder import ReportBuilder
from .render.pdf import save_pdf


@click.group()
@click.version_option(version="1.0.0", prog_name="mrr-automation")
def cli():
    """MRR Automation — H Heuristics Market Research PDF Report Generator.

    Produces professional 20-60 page market research reports
    with real data, data visuals, and publication-ready formatting.
    """


@cli.command()
@click.argument("spec_path", type=click.Path(exists=True))
@click.option("-o", "--output", default=None, help="Output PDF path (default: output/<title>.pdf)")
@click.option("--seed", type=int, default=None, help="Design seed for reproducible themes")
@click.option("--no-brand", is_flag=True, help="Use algorithmic theme instead of H Heuristics brand")
@click.option("--cache-dir", default="./cache", help="API cache directory")
def generate(spec_path: str, output: str | None, seed: int | None,
             no_brand: bool, cache_dir: str):
    """Generate a PDF report from a YAML specification."""
    click.echo(f"\U0001f4c4 Loading spec: {spec_path}")

    try:
        spec = load_spec(spec_path)
    except SpecError as e:
        click.echo(f"\u274c Spec error: {e}", err=True)
        sys.exit(1)

    meta = spec["meta"]
    click.echo(f"   Title: {meta['title']}")
    click.echo(f"   Author: {meta.get('author', 'H Heuristics Research')}")
    click.echo(f"   Date: {meta.get('date', 'N/A')}")

    # Determine seed
    if seed is None:
        seed = meta.get("seed")
    if seed is None:
        seed = random.randint(0, 2**31 - 1)

    # Theme
    use_brand = not no_brand
    if use_brand:
        click.echo("\U0001f3a8 Using H Heuristics brand theme")
        theme = H_HEURISTICS_THEME
    else:
        click.echo(f"\U0001f3a8 Generating algorithmic theme (seed={seed})...")
        theme = generate_theme(seed, page_size=meta.get("pages", {}).get("size", "A4"))
        click.echo(f"   Palette: {theme.palette.primary} / {theme.palette.secondary} / {theme.palette.accent}")
        click.echo(f"   Cover: {theme.cover_archetype}")

    # Count sections/chapters for progress
    sections = spec.get("sections", [])
    chapter_count = sum(1 for s in sections if s.get("type") == "chapter")
    chart_count = sum(1 for s in sections if s.get("type") == "chart")
    click.echo(f"\U0001f4ca Report structure: {chapter_count} chapters, {chart_count} charts")

    # Build
    click.echo("\U0001f527 Building report...")
    builder = ReportBuilder(spec, theme=theme, use_brand=use_brand, data_cache_dir=cache_dir)

    try:
        pdf_buf = builder.build()
    except Exception as e:
        click.echo(f"\u274c Build error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Determine output path
    if output is None:
        safe_title = meta["title"].lower().replace(" ", "_").replace("/", "-")[:60]
        output = f"output/{safe_title}.pdf"

    click.echo(f"\U0001f4d5 Saving PDF \u2192 {output}...")
    out_path = save_pdf(pdf_buf, output)

    file_size = out_path.stat().st_size
    click.echo(f"\u2705 Report generated: {out_path} ({file_size / 1024:.1f} KB)")
    click.echo(f"   Theme seed: {seed} (save this to reproduce the design)")


@cli.command()
@click.option("--seed", type=int, default=None, help="Design seed (random if omitted)")
def theme_preview(seed: int | None):
    """Preview a theme — shows palette, typography, and cover style."""
    if seed is None:
        seed = random.randint(0, 2**31 - 1)

    theme = generate_theme(seed)
    p = theme.palette

    click.echo(f"Theme: {theme.name}")
    click.echo(f"Seed:  {seed}")
    click.echo(f"Cover: {theme.cover_archetype} ({theme.decorative_density})")
    click.echo(f"")
    click.echo(f"Primary:        {p.primary}")
    click.echo(f"Secondary:      {p.secondary}")
    click.echo(f"Accent:         {p.accent}")
    click.echo(f"Neutral Dark:   {p.neutral_dark}")
    click.echo(f"Neutral Light:  {p.neutral_light}")
    click.echo(f"Neutral Mid:    {p.neutral_mid}")
    click.echo(f"Chart Colors:   {', '.join(p.chart_colors[:5])}")
    click.echo(f"")
    click.echo(f"Heading Font:   {theme.typography.heading_font}")
    click.echo(f"Body Font:      {theme.typography.body_font}")
    click.echo(f"Body Size:      {theme.typography.body_size}pt")
    click.echo(f"")
    click.echo(f"Page: {theme.layout.page_width:.0f}×{theme.layout.page_height:.0f}pt")
    click.echo(f"Margins: T:{theme.layout.margin_top:.0f} B:{theme.layout.margin_bottom:.0f} "
               f"L:{theme.layout.margin_left:.0f} R:{theme.layout.margin_right:.0f}pt")


if __name__ == "__main__":
    cli()
