"""Earnings call transcripts via SEC EDGAR full-text search."""
import httpx
from typing import List
import logging

logger = logging.getLogger(__name__)

EDGAR_FULL_TEXT_SEARCH = "https://efts.sec.gov/LATEST/search-index?q={query}&dateRange=custom&startdt={start_dt}&forms=8-K"
EDGAR_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
EDGAR_FULL_SEARCH = "https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22+%22earnings+call%22&forms=8-K&dateRange=custom&startdt=2023-01-01"


class EarningsCallFetcher:
    HEADERS = {
        "User-Agent": "AI-Finance-Research contact@example.com",
        "Accept-Encoding": "gzip, deflate",
    }

    def fetch_recent_filings(self, ticker: str, max_items: int = 3) -> List[dict]:
        """Fetch recent 8-K filings mentioning earnings from EDGAR."""
        try:
            url = f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22+%22earnings%22&forms=8-K&dateRange=custom&startdt=2023-01-01&hits.hits._source=period_of_report,entity_name,file_date,form_type,biz_location"
            with httpx.Client(timeout=15, headers=self.HEADERS) as client:
                resp = client.get(url)
                if resp.status_code != 200:
                    return []
                data = resp.json()
                hits = data.get("hits", {}).get("hits", [])
                results = []
                for hit in hits[:max_items]:
                    src = hit.get("_source", {})
                    results.append({
                        "entity_name": src.get("entity_name", ticker),
                        "file_date": src.get("file_date", ""),
                        "form_type": src.get("form_type", "8-K"),
                        "period": src.get("period_of_report", ""),
                        "id": hit.get("_id", ""),
                    })
                return results
        except Exception as e:
            logger.error(f"Error fetching EDGAR earnings for {ticker}: {e}")
            return []

    def to_text_summary(self, ticker: str) -> str:
        """Format earnings call info as text for LLM context."""
        filings = self.fetch_recent_filings(ticker)
        if not filings:
            return f"No recent SEC 8-K earnings filings found for {ticker}"

        lines = [f"# Recent SEC 8-K Filings for {ticker}\n"]
        for f in filings:
            lines.append(f"- **{f['entity_name']}** | {f['form_type']} | Filed: {f['file_date']} | Period: {f['period']}")

        return "\n".join(lines)


earnings_call_fetcher = EarningsCallFetcher()
