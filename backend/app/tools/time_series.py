"""Time series analysis for price data."""
import pandas as pd
import numpy as np
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class TimeSeriesAnalyzer:
    def compute_price_features(self, ticker: str, ohlcv_df: pd.DataFrame) -> dict:
        """Compute price-based features from OHLCV data."""
        if ohlcv_df is None or ohlcv_df.empty:
            return {}

        features = {}
        try:
            close = ohlcv_df["Close"].dropna()
            if len(close) < 20:
                return {}

            # Returns
            daily_returns = close.pct_change().dropna()
            features["daily_return_mean"] = float(daily_returns.mean())
            features["daily_volatility"] = float(daily_returns.std())
            features["annualized_volatility"] = float(daily_returns.std() * np.sqrt(252))

            # Price metrics
            features["current_price"] = float(close.iloc[-1])
            features["price_52w_high"] = float(close.tail(252).max())
            features["price_52w_low"] = float(close.tail(252).min())
            features["pct_from_52w_high"] = float(
                (close.iloc[-1] - features["price_52w_high"]) / features["price_52w_high"]
            )
            features["pct_from_52w_low"] = float(
                (close.iloc[-1] - features["price_52w_low"]) / features["price_52w_low"]
            )

            # Momentum
            if len(close) >= 252:
                features["momentum_12m"] = float(close.iloc[-1] / close.iloc[-252] - 1)
            if len(close) >= 63:
                features["momentum_3m"] = float(close.iloc[-1] / close.iloc[-63] - 1)
            if len(close) >= 21:
                features["momentum_1m"] = float(close.iloc[-1] / close.iloc[-21] - 1)

            # Moving averages
            if len(close) >= 200:
                ma200 = close.tail(200).mean()
                features["ma200"] = float(ma200)
                features["above_ma200"] = bool(close.iloc[-1] > ma200)
            if len(close) >= 50:
                ma50 = close.tail(50).mean()
                features["ma50"] = float(ma50)

            # Sharpe ratio (annualized, assuming risk-free rate of 4%)
            risk_free = 0.04 / 252
            excess_returns = daily_returns - risk_free
            if daily_returns.std() > 0:
                features["sharpe_ratio"] = float(
                    excess_returns.mean() / daily_returns.std() * np.sqrt(252)
                )

            # Detect anomalies (days with |return| > 3 std)
            threshold = daily_returns.std() * 3
            anomaly_days = (daily_returns.abs() > threshold).sum()
            features["anomaly_days_count"] = int(anomaly_days)

        except Exception as e:
            logger.error(f"Error computing price features for {ticker}: {e}")

        return features

    def format_text(self, ticker: str, features: dict) -> str:
        """Format price features as text for LLM context."""
        if not features:
            return f"No price data available for {ticker}"

        lines = [f"# Price & Market Data for {ticker}\n"]
        line_map = {
            "current_price": ("Current Price", "$"),
            "price_52w_high": ("52-Week High", "$"),
            "price_52w_low": ("52-Week Low", "$"),
            "pct_from_52w_high": ("% From 52W High", "%"),
            "annualized_volatility": ("Annualized Volatility", "%"),
            "momentum_12m": ("12-Month Momentum", "%"),
            "momentum_3m": ("3-Month Momentum", "%"),
            "sharpe_ratio": ("Sharpe Ratio (1Y)", ""),
            "above_ma200": ("Above 200-Day MA", ""),
        }
        for key, (label, unit) in line_map.items():
            val = features.get(key)
            if val is None:
                continue
            if unit == "%":
                lines.append(f"- {label}: {val * 100:.1f}%")
            elif unit == "$":
                lines.append(f"- {label}: ${val:,.2f}")
            else:
                lines.append(f"- {label}: {val}")

        return "\n".join(lines)


time_series_analyzer = TimeSeriesAnalyzer()
