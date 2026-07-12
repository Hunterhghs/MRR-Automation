"""World Bank API client — fetches development indicators.

API docs: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-api
"""

import time
from typing import Any

import requests

from .cache import DataCache

BASE_URL = "https://api.worldbank.org/v2"

COMMON_INDICATORS = {
    "NY.GDP.MKTP.CD": "GDP (current US$)",
    "NY.GDP.MKTP.KD.ZG": "GDP growth (annual %)",
    "NY.GDP.PCAP.CD": "GDP per capita (current US$)",
    "SP.POP.TOTL": "Population, total",
    "SP.POP.GROW": "Population growth (annual %)",
    "SP.URB.TOTL.IN.ZS": "Urban population (% of total)",
    "SL.UEM.TOTL.ZS": "Unemployment, total (% of total labor force)",
    "FP.CPI.TOTL.ZG": "Inflation, consumer prices (annual %)",
    "NE.EXP.GNFS.ZS": "Exports of goods and services (% of GDP)",
    "NE.IMP.GNFS.ZS": "Imports of goods and services (% of GDP)",
    "BX.KLT.DINV.WD.GD.ZS": "Foreign direct investment, net inflows (% of GDP)",
    "IT.NET.USER.ZS": "Individuals using the Internet (% of population)",
    "EG.USE.ELEC.KH.PC": "Electric power consumption (kWh per capita)",
    "EN.ATM.CO2E.KT": "CO2 emissions (kt)",
    "SH.XPD.CHEX.GD.ZS": "Current health expenditure (% of GDP)",
    "SE.PRM.ENRR": "School enrollment, primary (% gross)",
    "IC.BUS.EASE.XQ": "Ease of doing business score",
    "TX.VAL.TECH.MF.ZS": "High-technology exports (% of manufactured exports)",
    "MS.MIL.XPND.GD.ZS": "Military expenditure (% of GDP)",
    "IT.CEL.SETS.P2": "Mobile cellular subscriptions (per 100 people)",
    "BX.TRF.PWKR.DT.GD.ZS": "Personal remittances, received (% of GDP)",
    "NY.GDP.DEFL.KD.ZG": "GDP deflator (annual %)",
}

COUNTRY_CODES = {
    "usa": "USA", "united states": "USA", "us": "USA",
    "chn": "CHN", "china": "CHN",
    "jpn": "JPN", "japan": "JPN",
    "deu": "DEU", "germany": "DEU",
    "gbr": "GBR", "united kingdom": "GBR", "uk": "GBR",
    "fra": "FRA", "france": "FRA",
    "ind": "IND", "india": "IND",
    "bra": "BRA", "brazil": "BRA",
    "ita": "ITA", "italy": "ITA",
    "can": "CAN", "canada": "CAN",
    "rus": "RUS", "russia": "RUS",
    "kor": "KOR", "south korea": "KOR", "korea": "KOR",
    "aus": "AUS", "australia": "AUS",
    "mex": "MEX", "mexico": "MEX",
    "idn": "IDN", "indonesia": "IDN",
    "tur": "TUR", "turkey": "TUR",
    "sau": "SAU", "saudi arabia": "SAU",
    "zaf": "ZAF", "south africa": "ZAF",
    "nga": "NGA", "nigeria": "NGA",
    "egy": "EGY", "egypt": "EGY",
    "vnm": "VNM", "vietnam": "VNM",
    "tha": "THA", "thailand": "THA",
    "phl": "PHL", "philippines": "PHL",
    "pak": "PAK", "pakistan": "PAK",
    "bgd": "BGD", "bangladesh": "BGD",
    "arg": "ARG", "argentina": "ARG",
    "col": "COL", "colombia": "COL",
    "chl": "CHL", "chile": "CHL",
    "per": "PER", "peru": "PER",
    "mys": "MYS", "malaysia": "MYS",
    "sgp": "SGP", "singapore": "SGP",
    "are": "ARE", "uae": "ARE", "united arab emirates": "ARE",
    "ken": "KEN", "kenya": "KEN",
    "eth": "ETH", "ethiopia": "ETH",
    "gha": "GHA", "ghana": "GHA",
    "rwa": "RWA", "rwanda": "RWA",
    "wld": "WLD", "world": "WLD",
    "eui": "EUI", "european union": "EUI", "eu": "EUI",
    "esp": "ESP", "spain": "ESP",
    "nld": "NLD", "netherlands": "NLD",
    "che": "CHE", "switzerland": "CHE",
    "swe": "SWE", "sweden": "SWE",
    "nor": "NOR", "norway": "NOR",
    "dnk": "DNK", "denmark": "DNK",
    "fin": "FIN", "finland": "FIN",
    "bel": "BEL", "belgium": "BEL",
    "aut": "AUT", "austria": "AUT",
    "pol": "POL", "poland": "POL",
    "prt": "PRT", "portugal": "PRT",
    "grc": "GRC", "greece": "GRC",
    "irl": "IRL", "ireland": "IRL",
    "nzl": "NZL", "new zealand": "NZL",
    "isr": "ISR", "israel": "ISR",
}


def resolve_country(name: str) -> str:
    """Resolve a country name or code to an ISO3 code."""
    key = name.lower().strip()
    return COUNTRY_CODES.get(key, name.upper())


class WorldBankAPI:
    """Client for the World Bank Data API with caching."""

    def __init__(self, cache: DataCache | None = None):
        self.cache = cache or DataCache()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "HeuristicsReportGenerator/1.0",
        })

    def get_indicator(
        self,
        indicator: str,
        countries: list[str] | None = None,
        date_range: tuple[int, int] | None = None,
        per_page: int = 500,
    ) -> dict[str, Any]:
        """Fetch a World Bank indicator for one or more countries."""
        if countries is None:
            countries = ["WLD"]

        iso_codes = [resolve_country(c) for c in countries]
        codes_str = ";".join(iso_codes)

        params = {
            "format": "json",
            "per_page": min(per_page, 1000),
        }
        if date_range:
            params["date"] = f"{date_range[0]}:{date_range[1]}"

        cached = self.cache.get("world_bank", indicator, {
            "countries": sorted(iso_codes),
            "date_range": list(date_range) if date_range else None,
        })
        if cached is not None:
            return cached

        url = f"{BASE_URL}/country/{codes_str}/indicator/{indicator}"
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()

        raw = response.json()
        if not raw or len(raw) < 2:
            return {"_meta": {"indicator": indicator, "label": indicator, "error": "No data returned"}}

        meta_page = raw[0]
        data_page = raw[1]

        by_country: dict[str, list[dict]] = {}
        for entry in data_page:
            if entry.get("value") is None:
                continue
            code = entry["countryiso3code"]
            by_country.setdefault(code, []).append({
                "year": int(entry["date"]),
                "value": entry["value"],
                "country": entry["country"]["value"],
            })

        for code in by_country:
            by_country[code].sort(key=lambda x: x["year"])

        result = {
            "_meta": {
                "indicator": indicator,
                "label": meta_page.get("name", indicator) if isinstance(meta_page, dict) else indicator,
                "source": "World Bank",
                "last_updated": meta_page.get("lastupdated", "") if isinstance(meta_page, dict) else "",
            },
            **by_country,
        }

        self.cache.set("world_bank", indicator, result, {
            "countries": sorted(iso_codes),
            "date_range": list(date_range) if date_range else None,
        })

        time.sleep(0.3)
        return result

    def get_indicator_safe(
        self,
        indicator: str,
        countries: list[str] | None = None,
        date_range: tuple[int, int] | None = None,
        max_retries: int = 2,
    ) -> dict[str, Any]:
        """Fetch with retries and graceful failure."""
        last_exc = None
        for attempt in range(max_retries + 1):
            try:
                return self.get_indicator(indicator, countries, date_range)
            except Exception as e:
                last_exc = e
                if attempt < max_retries:
                    time.sleep(1.0 * (attempt + 1))
        return {
            "_meta": {"indicator": indicator, "label": indicator, "error": str(last_exc)},
            "_error": str(last_exc),
        }

    def get_multiple_indicators(
        self,
        indicators: list[str],
        countries: list[str] | None = None,
        date_range: tuple[int, int] | None = None,
    ) -> dict[str, dict]:
        """Fetch multiple indicators at once."""
        results = {}
        for ind in indicators:
            results[ind] = self.get_indicator(ind, countries, date_range)
        return results
