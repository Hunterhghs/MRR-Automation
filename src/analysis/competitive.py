"""Competitive analysis — positioning matrices and benchmarking."""

import numpy as np


def build_competitive_matrix(
    companies: list[str],
    metrics: dict[str, list[float]],
) -> dict:
    """Build a competitive positioning matrix.

    Args:
        companies: List of company names.
        metrics: Dict mapping metric names to lists of values (one per company).

    Returns:
        Dict with matrix data and normalized scores.
    """
    n = len(companies)
    normalized = {}
    for metric_name, values in metrics.items():
        arr = np.array(values)
        vmin, vmax = arr.min(), arr.max()
        if vmax > vmin:
            normalized[metric_name] = ((arr - vmin) / (vmax - vmin)).tolist()
        else:
            normalized[metric_name] = [0.5] * n

    # Composite score (average of normalized)
    composite = np.mean(list(normalized.values()), axis=0).tolist()

    # Rank
    ranks = np.argsort(np.argsort(composite))[::-1] + 1  # 1-based, descending
    ranks = ranks.tolist()

    return {
        "companies": companies,
        "metrics": metrics,
        "normalized": normalized,
        "composite_score": composite,
        "rank": ranks,
    }


def market_share_analysis(
    revenues: dict[str, float],
) -> dict:
    """Calculate market shares from company revenues.

    Args:
        revenues: Dict mapping company names to revenue values.

    Returns:
        Dict with shares, total, and concentration metrics.
    """
    total = sum(revenues.values())
    shares = {k: (v / total * 100) if total > 0 else 0 for k, v in revenues.items()}

    # Sort by share descending
    sorted_shares = sorted(shares.values(), reverse=True)

    # Herfindahl-Hirschman Index (HHI)
    hhi = sum(s**2 for s in sorted_shares)

    # CR3, CR5 (concentration ratio)
    cr3 = sum(sorted_shares[:3]) if len(sorted_shares) >= 3 else sum(sorted_shares)
    cr5 = sum(sorted_shares[:5]) if len(sorted_shares) >= 5 else sum(sorted_shares)

    return {
        "shares": shares,
        "total_market": total,
        "hhi": hhi,
        "cr3": cr3,
        "cr5": cr5,
        "concentration": "high" if hhi > 2500 else "moderate" if hhi > 1500 else "low",
    }
