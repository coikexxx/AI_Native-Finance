"""Financial statements ingestion via yfinance."""
import yfinance as yf
import pandas as pd
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class FinancialsFetcher:
    def fetch_income_statement(self, ticker: str) -> pd.DataFrame:
        try:
            t = yf.Ticker(ticker)
            df = t.financials  # Annual income statement
            return df if df is not None and not df.empty else pd.DataFrame()
        except Exception as e:
            logger.error(f"Error fetching income statement for {ticker}: {e}")
            return pd.DataFrame()

    def fetch_balance_sheet(self, ticker: str) -> pd.DataFrame:
        try:
            t = yf.Ticker(ticker)
            df = t.balance_sheet
            return df if df is not None and not df.empty else pd.DataFrame()
        except Exception as e:
            logger.error(f"Error fetching balance sheet for {ticker}: {e}")
            return pd.DataFrame()

    def fetch_cash_flow(self, ticker: str) -> pd.DataFrame:
        try:
            t = yf.Ticker(ticker)
            df = t.cashflow
            return df if df is not None and not df.empty else pd.DataFrame()
        except Exception as e:
            logger.error(f"Error fetching cash flow for {ticker}: {e}")
            return pd.DataFrame()

    def fetch_quarterly_income(self, ticker: str) -> pd.DataFrame:
        try:
            t = yf.Ticker(ticker)
            df = t.quarterly_financials
            return df if df is not None and not df.empty else pd.DataFrame()
        except Exception as e:
            logger.error(f"Error fetching quarterly income for {ticker}: {e}")
            return pd.DataFrame()

    def fetch_earnings_calendar(self, ticker: str) -> dict:
        """Fetch upcoming earnings dates."""
        try:
            t = yf.Ticker(ticker)
            cal = t.calendar
            if cal is not None and not cal.empty:
                return cal.to_dict()
            return {}
        except Exception as e:
            logger.error(f"Error fetching calendar for {ticker}: {e}")
            return {}

    def to_text_summary(self, ticker: str) -> str:
        """Convert financials to a text summary for LLM context."""
        lines = [f"# Financial Statements for {ticker}"]

        income = self.fetch_income_statement(ticker)
        if not income.empty:
            lines.append("\n## Income Statement (Annual)")
            lines.append(income.to_string())

        balance = self.fetch_balance_sheet(ticker)
        if not balance.empty:
            lines.append("\n## Balance Sheet (Annual)")
            lines.append(balance.to_string())

        cashflow = self.fetch_cash_flow(ticker)
        if not cashflow.empty:
            lines.append("\n## Cash Flow Statement (Annual)")
            lines.append(cashflow.to_string())

        return "\n".join(lines)


financials_fetcher = FinancialsFetcher()
