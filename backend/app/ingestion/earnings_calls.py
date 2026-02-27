"""
Regulatory filings ingestion — market-aware.

For A-shares and HK stocks, SEC EDGAR is not applicable.
We return a contextual note pointing analysts to the correct disclosure
platforms and skip the EDGAR HTTP call entirely.
"""
import httpx
from typing import List
import logging

logger = logging.getLogger(__name__)

# Market-appropriate disclosure platform notes (used instead of EDGAR)
_MARKET_FILING_NOTES: dict[str, str] = {
    "a_share": (
        "# A股信息披露说明\n"
        "A股上市公司定期报告（年报、半年报、季报）和临时公告通过以下平台披露：\n"
        "- 巨潮资讯网（cninfo.com.cn）：官方指定披露平台\n"
        "- 上海证券交易所（sse.com.cn）：沪市公司公告\n"
        "- 深圳证券交易所（szse.cn）：深市公司公告\n"
        "SEC EDGAR 不适用于A股。请基于yfinance提供的财务数据及新闻进行分析。"
    ),
    "hk": (
        "# 港股信息披露说明\n"
        "香港上市公司公告和财务报告通过以下平台披露：\n"
        "- 港交所披露易（hkexnews.hk）：官方指定披露平台\n"
        "- 香港联合交易所（hkex.com.hk）：上市公司公告\n"
        "SEC EDGAR 不适用于港股（除非为在美国同步上市的ADR）。"
    ),
    "crypto": (
        "# 比特币监管披露说明\n"
        "比特币（BTC）为去中心化资产，无传统监管披露义务。\n"
        "链上数据和网络统计可通过以下平台查询：\n"
        "- Glassnode（glassnode.com）：链上指标（活跃地址、MVRV等）\n"
        "- CoinMetrics（coinmetrics.io）：网络数据\n"
        "- Bitcoin Core GitHub（github.com/bitcoin/bitcoin）：协议开发动态"
    ),
}


class EarningsCallFetcher:
    HEADERS = {
        "User-Agent": "AI-Finance-Research contact@example.com",
        "Accept-Encoding": "gzip, deflate",
    }

    def fetch_recent_filings(self, ticker: str, max_items: int = 3) -> List[dict]:
        """Fetch recent 8-K filings from SEC EDGAR (US-listed companies only)."""
        try:
            url = (
                f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22+%22earnings%22"
                "&forms=8-K&dateRange=custom&startdt=2023-01-01"
                "&hits.hits._source=period_of_report,entity_name,file_date,form_type,biz_location"
            )
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

    def to_text_summary(self, ticker: str, market: str = "unknown") -> str:
        """
        Return filings context for LLM.
        Non-US markets get a disclosure-platform note instead of EDGAR results.
        """
        if market in _MARKET_FILING_NOTES:
            return _MARKET_FILING_NOTES[market]

        # Unknown / US-listed: attempt EDGAR lookup
        filings = self.fetch_recent_filings(ticker)
        if not filings:
            return f"No recent SEC 8-K earnings filings found for {ticker}"

        lines = [f"# Recent SEC 8-K Filings for {ticker}\n"]
        for f in filings:
            lines.append(
                f"- **{f['entity_name']}** | {f['form_type']} "
                f"| Filed: {f['file_date']} | Period: {f['period']}"
            )
        return "\n".join(lines)


earnings_call_fetcher = EarningsCallFetcher()
