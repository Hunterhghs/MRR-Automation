"""Market sizing analysis — TAM, SAM, SOM calculations."""

import numpy as np


def calculate_tam_sam_som(
    total_addressable: float,
    serviceable_pct: float = 0.4,
    obtainable_pct: float = 0.15,
) -> dict:
    """Calculate TAM, SAM, SOM from total addressable market.

    Args:
        total_addressable: Total addressable market value.
        serviceable_pct: Fraction that is serviceable (0.0–1.0).
        obtainable_pct: Fraction of SAM that is obtainable (0.0–1.0).

    Returns:
        Dict with tam, sam, som values.
    """
    sam = total_addressable * serviceable_pct
    som = sam * obtainable_pct
    return {
        "tam": total_addressable,
        "sam": sam,
        "som": som,
        "sam_pct": serviceable_pct * 100,
        "som_of_tam_pct": obtainable_pct * serviceable_pct * 100,
    }


def project_growth(
    current_value: float,
    cagr: float,
    years: int,
) -> list[dict]:
    """Project growth at a given CAGR.

    Args:
        current_value: Starting market size.
        cagr: Compound annual growth rate as decimal (e.g., 0.15 = 15%).
        years: Number of years to project.

    Returns:
        List of {year, value} dicts.
    """
    projections = []
    for y in range(years + 1):
        projections.append({
            "year": y,
            "value": current_value * (1 + cagr) ** y,
        })
    return projections


def calculate_cagr(start_value: float, end_value: float, years: int) -> float:
    """Calculate compound annual growth rate."""
    if start_value <= 0 or years <= 0:
        return 0.0
    return (end_value / start_value) ** (1.0 / years) - 1
