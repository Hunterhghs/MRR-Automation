"""Extended chart engine — matplotlib-based charts for ReportLab embedding.

Supports 12+ chart types, all styled to the report Theme.
Each chart returns a BytesIO buffer ready for ReportLab Image flowable.

Chart types:
  line, bar, horizontal_bar, stacked_bar, grouped_bar,
  area, stacked_area, scatter, bubble, waterfall,
  donut, heatmap, radar, slope
"""

import io
import math
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

from ..design.theme import Theme


# ── Style application ──────────────────────────────────────────────────

def _apply_theme(theme: Theme):
    """Configure matplotlib global style from a Theme."""
    p = theme.palette
    plt.rcParams.update({
        "figure.dpi": 200,
        "figure.facecolor": p.neutral_light,
        "axes.facecolor": "#ffffff",
        "axes.edgecolor": p.neutral_mid,
        "axes.labelcolor": p.neutral_dark,
        "axes.titlecolor": p.neutral_dark,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.color": p.neutral_mid,
        "xtick.color": p.neutral_dark,
        "ytick.color": p.neutral_dark,
        "text.color": p.neutral_dark,
        "font.family": "sans-serif",
        "font.size": 8,
        "legend.edgecolor": p.neutral_mid,
        "legend.facecolor": "#ffffff",
        "legend.fontsize": 7,
        "lines.linewidth": 1.8,
    })


def _to_buffer(fig: plt.Figure, dpi: int = 200) -> io.BytesIO:
    """Render figure to a BytesIO PNG buffer."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight",
                pad_inches=0.1, facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    return buf


def _figsize_for_width(width_pt: float, aspect: float = 2.0) -> tuple[float, float]:
    """Calculate figsize in inches for a given width in points."""
    width_in = width_pt / 72.0
    height_in = width_in / aspect
    return (width_in, height_in)


# ── Chart generators ───────────────────────────────────────────────────

def line_chart(
    data: dict[str, list[dict]],
    theme: Theme,
    width_pt: float = 450,
    aspect: float = 2.2,
    title: str = "",
    x_label: str = "",
    y_label: str = "",
    show_markers: bool = True,
) -> io.BytesIO:
    """Multi-series line chart."""
    _apply_theme(theme)
    p = theme.palette
    figsize = _figsize_for_width(width_pt, aspect)
    fig, ax = plt.subplots(figsize=figsize)

    colors = p.chart_colors[: max(len(data), 1)]

    for i, (label, points) in enumerate(data.items()):
        if not points:
            continue
        years = [pt.get("year", pt.get("date", 0)) for pt in points]
        values = [pt["value"] for pt in points]
        color = colors[i % len(colors)]
        marker = "o" if show_markers and len(points) < 30 else None
        ax.plot(years, values, marker=marker, markersize=3,
                label=label, color=color, linewidth=2.0)

    ax.set_title(title, fontweight="bold", fontsize=10, pad=8, color=p.neutral_dark)
    ax.set_xlabel(x_label, fontsize=7)
    ax.set_ylabel(y_label, fontsize=7)
    if len(data) > 1:
        ax.legend(frameon=True, fancybox=False, fontsize=7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Format large numbers
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, p: f"{x:,.0f}" if abs(x) < 1e6 else f"{x/1e6:,.1f}M"
        if abs(x) < 1e9 else f"{x/1e9:,.1f}B"
    ))

    fig.tight_layout()
    return _to_buffer(fig)


def bar_chart(
    data: dict[str, list[dict] | float],
    theme: Theme,
    width_pt: float = 450,
    aspect: float = 2.0,
    title: str = "",
    x_label: str = "",
    y_label: str = "",
    horizontal: bool = False,
) -> io.BytesIO:
    """Bar chart (vertical or horizontal)."""
    _apply_theme(theme)
    p = theme.palette
    figsize = _figsize_for_width(width_pt, aspect)
    fig, ax = plt.subplots(figsize=figsize)

    labels = list(data.keys())
    values = []
    for v in data.values():
        if isinstance(v, list) and v:
            values.append(v[-1]["value"])
        elif isinstance(v, (int, float)):
            values.append(v)
        else:
            values.append(0)

    colors = p.chart_colors[: len(labels)]

    if horizontal:
        bars = ax.barh(labels, values, color=colors, edgecolor="#ffffff", linewidth=0.5)
        ax.set_xlabel(y_label, fontsize=7)
    else:
        bars = ax.bar(labels, values, color=colors, edgecolor="#ffffff", linewidth=0.5)
        ax.set_ylabel(y_label, fontsize=7)
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=7)

    ax.set_title(title, fontweight="bold", fontsize=10, pad=8, color=p.neutral_dark)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    return _to_buffer(fig)


def grouped_bar_chart(
    categories: list[str],
    series: dict[str, list[float]],
    theme: Theme,
    width_pt: float = 450,
    aspect: float = 2.0,
    title: str = "",
    x_label: str = "",
    y_label: str = "",
) -> io.BytesIO:
    """Grouped bar chart with multiple series per category."""
    _apply_theme(theme)
    p = theme.palette

    n_cats = len(categories)
    n_series = len(series)
    bar_width = 0.75 / n_series

    figsize = _figsize_for_width(width_pt, aspect)
    fig, ax = plt.subplots(figsize=figsize)
    x = np.arange(n_cats)

    for i, (label, values) in enumerate(series.items()):
        offset = (i - n_series / 2 + 0.5) * bar_width
        color = p.chart_colors[i % len(p.chart_colors)]
        ax.bar(x + offset, values, bar_width, label=label, color=color,
               edgecolor="#ffffff", linewidth=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=7, rotation=30, ha="right")
    ax.set_title(title, fontweight="bold", fontsize=10, pad=8, color=p.neutral_dark)
    ax.set_xlabel(x_label, fontsize=7)
    ax.set_ylabel(y_label, fontsize=7)
    ax.legend(fontsize=7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    return _to_buffer(fig)


def stacked_area_chart(
    data: dict[str, list[dict]],
    theme: Theme,
    width_pt: float = 450,
    aspect: float = 2.2,
    title: str = "",
    x_label: str = "",
    y_label: str = "",
    normalize: bool = False,
) -> io.BytesIO:
    """Stacked area chart."""
    _apply_theme(theme)
    p = theme.palette

    figsize = _figsize_for_width(width_pt, aspect)
    fig, ax = plt.subplots(figsize=figsize)

    # Align all series to common x values
    all_years = set()
    for points in data.values():
        for pt in points:
            all_years.add(pt.get("year", pt.get("date", 0)))
    sorted_years = sorted(all_years)

    aligned = {}
    for label, points in data.items():
        year_map = {pt.get("year", pt.get("date", 0)): pt["value"] for pt in points}
        aligned[label] = [year_map.get(y, 0) for y in sorted_years]

    labels = list(aligned.keys())
    y_data = list(aligned.values())

    if normalize and len(aligned) > 1:
        # Normalize to 100%
        totals = np.sum(y_data, axis=0)
        totals[totals == 0] = 1
        y_data = [np.array(yd) / totals * 100 for yd in y_data]

    cum = np.zeros(len(sorted_years))
    for i in range(len(y_data)):
        color = p.chart_colors[i % len(p.chart_colors)]
        ax.fill_between(sorted_years, cum, cum + np.array(y_data[i]),
                        label=labels[i], color=color, alpha=0.85, linewidth=0.5)
        cum = cum + np.array(y_data[i])

    ax.set_title(title, fontweight="bold", fontsize=10, pad=8, color=p.neutral_dark)
    ax.set_xlabel(x_label, fontsize=7)
    ax.set_ylabel(y_label, fontsize=7)
    ax.legend(fontsize=7, loc="upper left")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    return _to_buffer(fig)


def scatter_chart(
    x_values: list[float],
    y_values: list[float],
    theme: Theme,
    width_pt: float = 400,
    aspect: float = 1.4,
    labels: list[str] | None = None,
    sizes: list[float] | None = None,
    title: str = "",
    x_label: str = "",
    y_label: str = "",
) -> io.BytesIO:
    """Scatter or bubble chart."""
    _apply_theme(theme)
    p = theme.palette

    figsize = _figsize_for_width(width_pt, aspect)
    fig, ax = plt.subplots(figsize=figsize)

    s = sizes if sizes else [50] * len(x_values)
    # Normalize sizes for bubbles
    if sizes:
        s_min, s_max = min(sizes), max(sizes)
        if s_max > s_min:
            s = [20 + 300 * (sz - s_min) / (s_max - s_min) for sz in sizes]

    ax.scatter(x_values, y_values, s=s, color=p.chart_colors[0],
               alpha=0.65, edgecolors="#ffffff", linewidth=0.5)

    if labels:
        for xi, yi, lbl in zip(x_values, y_values, labels):
            ax.annotate(lbl, (xi, yi), fontsize=6, color=p.neutral_dark,
                        xytext=(4, 4), textcoords="offset points")

    ax.set_title(title, fontweight="bold", fontsize=10, pad=8, color=p.neutral_dark)
    ax.set_xlabel(x_label, fontsize=7)
    ax.set_ylabel(y_label, fontsize=7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    return _to_buffer(fig)


def waterfall_chart(
    categories: list[str],
    values: list[float],
    theme: Theme,
    width_pt: float = 450,
    aspect: float = 2.0,
    title: str = "",
    y_label: str = "",
) -> io.BytesIO:
    """Waterfall chart (sequential build-up/break-down)."""
    _apply_theme(theme)
    p = theme.palette

    figsize = _figsize_for_width(width_pt, aspect)
    fig, ax = plt.subplots(figsize=figsize)

    # Compute bottoms
    running = [0.0]
    for v in values[:-1]:
        running.append(running[-1] + v)

    bottoms = running[:len(values)]
    colors = [p.semantic["positive"] if v >= 0 else p.semantic["negative"] for v in values]
    # First bar is the base, last is the total
    if len(colors) > 0:
        colors[0] = p.chart_colors[0]
    if len(colors) > 1:
        colors[-1] = p.chart_colors[0]

    bars = ax.bar(range(len(categories)), values, bottom=bottoms,
                  color=colors, edgecolor="#ffffff", linewidth=0.5)

    # Connect bars
    for i in range(len(values) - 1):
        y = bottoms[i] + values[i]
        ax.plot([i + 0.4, i + 0.6], [y, y], color=p.neutral_mid, linewidth=0.8, alpha=0.6)

    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels(categories, fontsize=7, rotation=30, ha="right")
    ax.set_title(title, fontweight="bold", fontsize=10, pad=8, color=p.neutral_dark)
    ax.set_ylabel(y_label, fontsize=7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    return _to_buffer(fig)


def donut_chart(
    data: dict[str, float],
    theme: Theme,
    width_pt: float = 350,
    aspect: float = 1.0,
    title: str = "",
    inner_radius: float = 0.55,
) -> io.BytesIO:
    """Donut chart with center label."""
    _apply_theme(theme)
    p = theme.palette

    figsize = _figsize_for_width(width_pt, aspect)
    fig, ax = plt.subplots(figsize=figsize)

    labels = list(data.keys())
    values = list(data.values())
    colors = p.chart_colors[: len(labels)]

    wedges, texts = ax.pie(
        values, labels=None, colors=colors,
        startangle=90, pctdistance=0.82,
        wedgeprops=dict(width=1 - inner_radius, edgecolor="#ffffff", linewidth=1.5)
    )

    # Center text
    total = sum(values)
    ax.text(0, 0, f"{total:,.0f}", ha="center", va="center",
            fontsize=14, fontweight="bold", color=p.neutral_dark)
    ax.text(0, -0.15, "Total", ha="center", va="center",
            fontsize=8, color=p.neutral_mid)

    # Legend
    legend_labels = [f"{l} ({v:,.0f})" for l, v in zip(labels, values)]
    ax.legend(wedges, legend_labels, fontsize=7,
              loc="center left", bbox_to_anchor=(1, 0.5))

    ax.set_title(title, fontweight="bold", fontsize=10, pad=8, color=p.neutral_dark)

    fig.tight_layout()
    return _to_buffer(fig)


def heatmap_chart(
    data: list[list[float]],
    row_labels: list[str],
    col_labels: list[str],
    theme: Theme,
    width_pt: float = 450,
    aspect: float = 0.9,
    title: str = "",
    cmap_name: str = "YlOrRd",
) -> io.BytesIO:
    """Heatmap for matrix data."""
    _apply_theme(theme)
    p = theme.palette

    figsize = _figsize_for_width(width_pt, aspect)
    fig, ax = plt.subplots(figsize=figsize)

    im = ax.imshow(data, cmap=cmap_name, aspect="auto")

    ax.set_xticks(range(len(col_labels)))
    ax.set_xticklabels(col_labels, fontsize=7, rotation=45, ha="right")
    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels(row_labels, fontsize=7)

    # Add text annotations
    for i in range(len(row_labels)):
        for j in range(len(col_labels)):
            val = data[i][j]
            text_color = "#ffffff" if val > np.mean(data) * 0.8 else p.neutral_dark
            ax.text(j, i, f"{val:.1f}", ha="center", va="center",
                    fontsize=7, color=text_color, fontweight="bold")

    ax.set_title(title, fontweight="bold", fontsize=10, pad=8, color=p.neutral_dark)
    fig.colorbar(im, ax=ax, shrink=0.8)

    fig.tight_layout()
    return _to_buffer(fig)


def radar_chart(
    categories: list[str],
    series: dict[str, list[float]],
    theme: Theme,
    width_pt: float = 400,
    aspect: float = 1.0,
    title: str = "",
) -> io.BytesIO:
    """Radar/spider chart for multi-dimensional comparison."""
    _apply_theme(theme)
    p = theme.palette

    n = len(categories)
    angles = [i * 2 * math.pi / n for i in range(n)]
    angles += angles[:1]  # Close the polygon

    figsize = _figsize_for_width(width_pt, aspect)
    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(polar=True))

    for i, (label, values) in enumerate(series.items()):
        vals = values + values[:1]
        color = p.chart_colors[i % len(p.chart_colors)]
        ax.fill(angles, vals, alpha=0.15, color=color)
        ax.plot(angles, vals, "o-", linewidth=1.5, color=color, label=label, markersize=4)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=7)
    ax.set_title(title, fontweight="bold", fontsize=10, pad=15, color=p.neutral_dark)
    ax.legend(fontsize=7, loc="upper right", bbox_to_anchor=(1.3, 1.1))
    ax.set_yticklabels([])

    fig.tight_layout()
    return _to_buffer(fig)


def slope_chart(
    categories: list[str],
    start_values: list[float],
    end_values: list[float],
    theme: Theme,
    width_pt: float = 400,
    aspect: float = 1.6,
    title: str = "",
    left_label: str = "Before",
    right_label: str = "After",
) -> io.BytesIO:
    """Slope chart showing change between two time points."""
    _apply_theme(theme)
    p = theme.palette

    figsize = _figsize_for_width(width_pt, aspect)
    fig, ax = plt.subplots(figsize=figsize)

    for i in range(len(categories)):
        y1, y2 = start_values[i], end_values[i]
        color = p.semantic["positive"] if y2 >= y1 else p.semantic["negative"]
        ax.plot([0, 1], [y1, y2], "-", color=color, linewidth=1.8, alpha=0.7, zorder=1)
        ax.scatter([0, 1], [y1, y2], s=30, color=color, zorder=2, edgecolors="#ffffff", linewidth=0.5)
        ax.text(-0.08, y1, f"{categories[i]}  {y1:,.0f}", ha="right", va="center", fontsize=6.5, color=p.neutral_dark)
        ax.text(1.08, y2, f"{y2:,.0f}  {categories[i]}", ha="left", va="center", fontsize=6.5, color=p.neutral_dark)

    ax.set_xlim(-0.4, 1.4)
    ax.set_xticks([0, 1])
    ax.set_xticklabels([left_label, right_label], fontsize=9, fontweight="bold")
    ax.set_title(title, fontweight="bold", fontsize=10, pad=8, color=p.neutral_dark)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.yaxis.set_visible(False)

    fig.tight_layout()
    return _to_buffer(fig)
