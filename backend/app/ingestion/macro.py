"""Macroeconomic data ingestion via FRED API (free)."""
import httpx
from typing import Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

KEY_SERIES = {
    "GDP": "Gross Domestic Product (quarterly)",
    "FEDFUNDS": "Federal Funds Rate (%)",
    "CPIAUCSL": "CPI - All Urban Consumers",
    "UNRATE": "Unemployment Rate (%)",
    "T10Y2Y": "10Y-2Y Treasury Spread (yield curve)",
    "VIXCLS": "CBOE Volatility Index (VIX)",
    "DGS10": "10-Year Treasury Constant Maturity Rate",
    "SP500": "S&P 500 Index",
}


class MacroFetcher:
    def fetch_series(self, series_id: str, limit: int = 12) -> list:
        """Fetch recent observations for a FRED series."""
        if not settings.fred_api_key:
            return []
        try:
            params = {
                "series_id": series_id,
                "api_key": settings.fred_api_key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": limit,
            }
            with httpx.Client(timeout=10) as client:
                resp = client.get(FRED_BASE, params=params)
                resp.raise_for_status()
                data = resp.json()
                return data.get("observations", [])
        except Exception as e:
            logger.error(f"Error fetching FRED series {series_id}: {e}")
            return []

    def to_text_summary(self) -> str:
        """Format key macro indicators as text for LLM context."""
        if not settings.fred_api_key:
            return "Macro data unavailable (FRED_API_KEY not set)"

        lines = ["# Macroeconomic Context (FRED Data)\n"]
        for series_id, label in KEY_SERIES.items():
            obs = self.fetch_series(series_id, limit=4)
            if obs:
                latest = [o for o in obs if o.get("value") != "."]
                if latest:
                    val = latest[0]["value"]
                    date = latest[0]["date"]
                    lines.append(f"- **{label}** ({series_id}): {val} as of {date}")
        return "\n".join(lines)


macro_fetcher = MacroFetcher()
