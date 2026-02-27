"""Market data ingestion via yfinance."""
import yfinance as yf
import pandas as pd
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class MarketDataFetcher:
    def fetch_ohlcv(self, ticker: str, period: str = "5y") -> pd.DataFrame:
        """Fetch OHLCV price history."""
        try:
            t = yf.Ticker(ticker)
            df = t.history(period=period, auto_adjust=True)
            if df.empty:
                logger.warning(f"No price data for {ticker}")
            return df
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {ticker}: {e}")
            return pd.DataFrame()

    def fetch_fast_price(self, ticker: str) -> Optional[float]:
        """Fetch current price quickly (for alert checks)."""
        try:
            t = yf.Ticker(ticker)
            price = t.fast_info.last_price
            return float(price) if price else None
        except Exception as e:
            logger.error(f"Error fetching price for {ticker}: {e}")
            return None

    def fetch_price_detail(self, ticker: str) -> dict:
        """Fetch price with change % and volume ratio for anomaly detection."""
        try:
            t = yf.Ticker(ticker)
            fi = t.fast_info
            price = fi.last_price
            prev_close = fi.previous_close
            last_volume = getattr(fi, "last_volume", None)
            avg_volume = getattr(fi, "three_month_average_volume", None)

            change_pct = None
            if price and prev_close and prev_close > 0:
                change_pct = (price - prev_close) / prev_close * 100

            volume_ratio = None
            if last_volume and avg_volume and avg_volume > 0:
                volume_ratio = last_volume / avg_volume

            return {
                "price": float(price) if price else None,
                "prev_close": float(prev_close) if prev_close else None,
                "change_pct": round(change_pct, 2) if change_pct is not None else None,
                "volume": int(last_volume) if last_volume else None,
                "avg_volume": int(avg_volume) if avg_volume else None,
                "volume_ratio": round(volume_ratio, 2) if volume_ratio is not None else None,
            }
        except Exception as e:
            logger.error(f"Error fetching price detail for {ticker}: {e}")
            return {"price": None, "prev_close": None, "change_pct": None,
                    "volume": None, "avg_volume": None, "volume_ratio": None}

    def fetch_options_info(self, ticker: str) -> dict:
        """Fetch options expiry dates and basic info."""
        try:
            t = yf.Ticker(ticker)
            return {"expiry_dates": list(t.options) if t.options else []}
        except Exception:
            return {"expiry_dates": []}


market_data_fetcher = MarketDataFetcher()
