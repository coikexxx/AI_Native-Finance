"""SQLite-backed feature store for computed financial ratios."""
import json
from datetime import datetime, timedelta
from typing import Optional
from app.config import settings
import logging
import sqlite3
import os

logger = logging.getLogger(__name__)

DB_PATH = settings.database_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")


class FeatureStore:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_table()

    def _init_table(self) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS financial_features (
                        ticker TEXT NOT NULL,
                        computed_at TIMESTAMP NOT NULL,
                        features_json TEXT NOT NULL,
                        PRIMARY KEY (ticker)
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Error initializing feature store: {e}")

    def save_features(self, ticker: str, features: dict) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO financial_features (ticker, computed_at, features_json)
                    VALUES (?, ?, ?)
                """, (ticker.upper(), datetime.utcnow().isoformat(), json.dumps(features)))
                conn.commit()
        except Exception as e:
            logger.error(f"Error saving features for {ticker}: {e}")

    def load_features(self, ticker: str, max_age_hours: int = 24) -> Optional[dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute(
                    "SELECT features_json, computed_at FROM financial_features WHERE ticker = ?",
                    (ticker.upper(),)
                ).fetchone()
                if not row:
                    return None
                computed_at = datetime.fromisoformat(row[1])
                if datetime.utcnow() - computed_at > timedelta(hours=max_age_hours):
                    return None  # Stale
                return json.loads(row[0])
        except Exception as e:
            logger.error(f"Error loading features for {ticker}: {e}")
            return None

    def compute_and_save(self, ticker: str, income_df, balance_df, cashflow_df) -> dict:
        """Compute financial ratios from DataFrames and persist."""
        features = {}
        try:
            import pandas as pd
            import numpy as np

            # Helper: safe get from DataFrame
            def get_val(df, row_name: str, col_idx: int = 0):
                if df is None or df.empty:
                    return None
                try:
                    matches = [r for r in df.index if row_name.lower() in str(r).lower()]
                    if not matches:
                        return None
                    val = df.loc[matches[0]].iloc[col_idx]
                    return float(val) if pd.notna(val) else None
                except Exception:
                    return None

            # Revenue metrics
            rev = get_val(income_df, "Total Revenue")
            rev_prev = get_val(income_df, "Total Revenue", 1)
            if rev and rev_prev and rev_prev != 0:
                features["revenue_growth_yoy"] = (rev - rev_prev) / abs(rev_prev)

            # Profitability
            net_income = get_val(income_df, "Net Income")
            gross_profit = get_val(income_df, "Gross Profit")
            ebit = get_val(income_df, "EBIT") or get_val(income_df, "Operating Income")

            if rev and rev > 0:
                if net_income is not None:
                    features["net_profit_margin"] = net_income / rev
                if gross_profit is not None:
                    features["gross_margin"] = gross_profit / rev
                if ebit is not None:
                    features["operating_margin"] = ebit / rev

            # Balance sheet ratios
            total_equity = get_val(balance_df, "Stockholders Equity") or get_val(balance_df, "Total Equity Gross Minority Interest")
            total_debt = get_val(balance_df, "Total Debt") or get_val(balance_df, "Long Term Debt")
            total_assets = get_val(balance_df, "Total Assets")
            current_assets = get_val(balance_df, "Current Assets")
            current_liabilities = get_val(balance_df, "Current Liabilities")

            if total_equity and total_equity > 0 and net_income:
                features["roe"] = net_income / total_equity
            if total_assets and total_assets > 0 and net_income:
                features["roa"] = net_income / total_assets
            if total_equity and total_equity > 0 and total_debt:
                features["debt_to_equity"] = total_debt / total_equity
            if current_assets and current_liabilities and current_liabilities > 0:
                features["current_ratio"] = current_assets / current_liabilities

            # FCF
            op_cf = get_val(cashflow_df, "Operating Cash Flow") or get_val(cashflow_df, "Cash From Operating Activities")
            capex = get_val(cashflow_df, "Capital Expenditure") or get_val(cashflow_df, "Purchases Of PPE")
            if op_cf is not None:
                features["operating_cash_flow"] = op_cf
                if capex is not None:
                    features["free_cash_flow"] = op_cf - abs(capex)
                    if rev and rev > 0:
                        features["fcf_margin"] = features["free_cash_flow"] / rev

            features["raw_revenue"] = rev
            features["raw_net_income"] = net_income
            features["raw_total_equity"] = total_equity
            features["raw_total_debt"] = total_debt

        except Exception as e:
            logger.error(f"Error computing features for {ticker}: {e}")

        self.save_features(ticker, features)
        return features


feature_store = FeatureStore()
