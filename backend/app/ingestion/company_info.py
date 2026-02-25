"""Company profile and info ingestion via yfinance."""
import yfinance as yf
from typing import Optional
import logging

logger = logging.getLogger(__name__)

IMPORTANT_INFO_KEYS = [
    "shortName", "longName", "sector", "industry", "country",
    "website", "longBusinessSummary", "fullTimeEmployees",
    "marketCap", "enterpriseValue", "trailingPE", "forwardPE",
    "priceToBook", "dividendYield", "beta", "52WeekChange",
    "sharesOutstanding", "floatShares", "heldPercentInsiders",
    "heldPercentInstitutions", "bookValue", "priceToSalesTrailing12Months",
    "profitMargins", "operatingMargins", "returnOnAssets", "returnOnEquity",
    "revenueGrowth", "earningsGrowth", "currentRatio", "debtToEquity",
    "totalRevenue", "grossProfits", "ebitda", "totalDebt", "freeCashflow",
    "operatingCashflow", "recommendationKey", "targetMeanPrice",
]


class CompanyInfoFetcher:
    def fetch_company_profile(self, ticker: str) -> dict:
        """Fetch company profile and key metrics."""
        try:
            t = yf.Ticker(ticker)
            info = t.info or {}
            # Filter to important keys only
            return {k: info.get(k) for k in IMPORTANT_INFO_KEYS if k in info}
        except Exception as e:
            logger.error(f"Error fetching company info for {ticker}: {e}")
            return {}

    def to_text_summary(self, ticker: str) -> str:
        """Format company info as text for LLM context."""
        info = self.fetch_company_profile(ticker)
        if not info:
            return f"No company info available for {ticker}"

        name = info.get("longName") or info.get("shortName") or ticker
        lines = [f"# Company Profile: {name} ({ticker})"]

        if info.get("longBusinessSummary"):
            lines.append(f"\n## Business Description\n{info['longBusinessSummary']}")

        lines.append("\n## Key Metrics")
        metric_map = {
            "sector": "Sector",
            "industry": "Industry",
            "country": "Country",
            "fullTimeEmployees": "Employees",
            "marketCap": "Market Cap",
            "trailingPE": "Trailing P/E",
            "forwardPE": "Forward P/E",
            "priceToBook": "Price/Book",
            "dividendYield": "Dividend Yield",
            "beta": "Beta",
            "returnOnEquity": "ROE",
            "returnOnAssets": "ROA",
            "profitMargins": "Net Profit Margin",
            "debtToEquity": "Debt/Equity",
            "currentRatio": "Current Ratio",
            "freeCashflow": "Free Cash Flow",
            "revenueGrowth": "Revenue Growth (YoY)",
            "earningsGrowth": "Earnings Growth (YoY)",
        }
        for key, label in metric_map.items():
            val = info.get(key)
            if val is not None:
                if isinstance(val, float) and abs(val) < 1 and val != 0:
                    lines.append(f"- {label}: {val:.2%}")
                elif isinstance(val, (int, float)) and abs(val) > 1_000_000:
                    lines.append(f"- {label}: ${val:,.0f}")
                else:
                    lines.append(f"- {label}: {val}")

        return "\n".join(lines)


company_info_fetcher = CompanyInfoFetcher()
