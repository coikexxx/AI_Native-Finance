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

    def fetch_options_info(self, ticker: str) -> dict:
        """Fetch options expiry dates and basic info."""
        try:
            t = yf.Ticker(ticker)
            return {"expiry_dates": list(t.options) if t.options else []}
        except Exception:
            return {"expiry_dates": []}


market_data_fetcher = MarketDataFetcher()
