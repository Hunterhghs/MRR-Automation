"""FRED (Federal Reserve Economic Data) API client.

FRED provides US and international economic data from the St. Louis Fed.
API docs: https://fred.stlouisfed.org/docs/api/fred/

Requires a FRED API key (free): https://fred.stlouisfed.org/docs/api/api_key.html
Set FRED_API_KEY environment variable or pass directly.
"""

import os
import time
from typing import Any

import requests

from .cache import DataCache

FRED_BASE = "https://api.stlouisfed.org/fred"


def _get_api_key() -> str:
    """Get FRED API key from environment."""
    key = os.environ.get("FRED_API_KEY", "")
    if not key:
        # Try a well-known demo key
        key = os.environ.get("FRED_API_KEY_DEMO", "")
    return key


class FREDAPI:
    """Client for the FRED economic data API."""

    def __init__(self, api_key: str | None = None, cache: DataCache | None = None):
        self.api_key = api_key or _get_api_key()
        self.cache = cache or DataCache()
        self.session = requests.Session()

    def _get(self, endpoint: str, **params) -> dict:
        """Make a FRED API request."""
        params["api_key"] = self.api_key
        params["file_type"] = "json"
        url = f"{FRED_BASE}{endpoint}"
        resp = self.session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_series(
        self,
        series_id: str,
        observation_start: str | None = None,
        observation_end: str | None = None,
        frequency: str | None = None,  # "d", "w", "m", "q", "a"
        units: str | None = None,       # "lin", "chg", "ch1", "pch", "pc1"
    ) -> dict[str, Any]:
        """Fetch a FRED series as time series data.

        Returns:
            Dict with 'meta' (series info) and 'data' (list of {date, value} dicts).
        """
        cache_key = {
            "series_id": series_id,
            "start": observation_start,
            "end": observation_end,
            "freq": frequency,
            "units": units,
        }
        cached = self.cache.get("fred", "series", cache_key)
        if cached is not None:
            return cached

        params = {"series_id": series_id}
        if observation_start:
            params["observation_start"] = observation_start
        if observation_end:
            params["observation_end"] = observation_end
        if frequency:
            params["frequency"] = frequency
        if units:
            params["units"] = units

        # Get series metadata
        meta = self._get("/series", series_id=series_id)

        # Get observations
        obs = self._get("/series/observations", **params)

        data = []
        for o in obs.get("observations", []):
            val = o.get("value", ".")
            if val == ".":
                continue
            try:
                data.append({
                    "date": o["date"],
                    "value": float(val),
                })
            except ValueError:
                data.append({
                    "date": o["date"],
                    "value": None,
                })

        result = {
            "meta": {
                "series_id": series_id,
                "title": meta.get("seriess", [{}])[0].get("title", series_id) if meta.get("seriess") else series_id,
                "units": meta.get("seriess", [{}])[0].get("units_short", "") if meta.get("seriess") else "",
                "frequency": meta.get("seriess", [{}])[0].get("frequency_short", "") if meta.get("seriess") else "",
                "source": "FRED (Federal Reserve Bank of St. Louis)",
            },
            "data": data,
        }

        self.cache.set("fred", "series", result, cache_key)
        time.sleep(0.2)
        return result

    def get_series_safe(self, series_id: str, **kwargs) -> dict[str, Any]:
        """Fetch with graceful failure."""
        try:
            return self.get_series(series_id, **kwargs)
        except Exception as e:
            return {
                "meta": {"series_id": series_id, "title": series_id, "error": str(e)},
                "data": [],
                "_error": str(e),
            }


# Common FRED series useful for market research
COMMON_FRED_SERIES = {
    "GDP": "Gross Domestic Product",
    "CPIAUCSL": "Consumer Price Index",
    "UNRATE": "Unemployment Rate",
    "FEDFUNDS": "Federal Funds Rate",
    "DGS10": "10-Year Treasury Yield",
    "T10YIE": "10-Year Breakeven Inflation Rate",
    "M2SL": "M2 Money Supply",
    "INDPRO": "Industrial Production Index",
    "HOUST": "Housing Starts",
    "RSAFS": "Retail Sales",
    "BOPGEXP": "Business Output: Government Expenditure",
    "PCEC96": "Real Personal Consumption Expenditures",
    "NASDAQCOM": "NASDAQ Composite Index",
    "SP500": "S&P 500 Index",
    "DTWEXBGS": "Trade Weighted U.S. Dollar Index",
    "T5YIFR": "5-Year Forward Inflation Expectation",
}
