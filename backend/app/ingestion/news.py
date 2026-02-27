"""News ingestion — Yahoo Finance RSS (all markets) + Sina Finance HTML (A-shares)."""
import feedparser
import httpx
from typing import List
import logging

logger = logging.getLogger(__name__)


class NewsItem:
    def __init__(self, title: str, summary: str, link: str, published: str):
        self.title = title
        self.summary = summary
        self.link = link
        self.published = published


# ── Sina Finance scraper (A-shares, Chinese-language) ─────────────────────────

class SinaFinanceNewsFetcher:
    """
    Fetches per-stock Chinese-language news from Sina Finance.
    URL: https://vip.stock.finance.sina.com.cn/corp/go.php/
         vCB_AllNewsStock/stockid/{6-digit}/page_type/lh.phtml
    """
    BASE_URL = (
        "https://vip.stock.finance.sina.com.cn/corp/go.php/"
        "vCB_AllNewsStock/stockid/{code}/page_type/lh.phtml"
    )
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://finance.sina.com.cn/",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }

    def fetch(self, stock_code: str, max_items: int = 15) -> List[NewsItem]:
        """Fetch A-share news from Sina Finance. stock_code = 6-digit code."""
        try:
            from bs4 import BeautifulSoup
            url = self.BASE_URL.format(code=stock_code)
            with httpx.Client(timeout=12, headers=self.HEADERS, follow_redirects=True) as client:
                resp = client.get(url)
                if resp.status_code != 200:
                    logger.warning(f"Sina Finance returned {resp.status_code} for {stock_code}")
                    return []

            soup = BeautifulSoup(resp.text, "html.parser")
            items: List[NewsItem] = []

            # Primary: datelist div
            datelist = soup.find("div", class_="datelist")
            if datelist:
                for a_tag in datelist.find_all("a", href=True)[:max_items]:
                    title = a_tag.get_text(strip=True)
                    if not title:
                        continue
                    link = a_tag["href"]
                    if link.startswith("//"):
                        link = "https:" + link
                    elif not link.startswith("http"):
                        link = "https://finance.sina.com.cn" + link
                    published = ""
                    parent = a_tag.parent
                    if parent:
                        span = parent.find("span")
                        if span:
                            published = span.get_text(strip=True)
                    items.append(NewsItem(title=title, summary="", link=link, published=published))
            else:
                # Fallback: tit links in table rows
                for td in soup.select("td.tit a")[:max_items]:
                    title = td.get_text(strip=True)
                    if not title:
                        continue
                    link = td.get("href", "")
                    if not link.startswith("http"):
                        link = "https://finance.sina.com.cn" + link
                    items.append(NewsItem(title=title, summary="", link=link, published=""))

            logger.info(f"Sina Finance: fetched {len(items)} items for {stock_code}")
            return items

        except Exception as e:
            logger.error(f"Sina Finance fetch failed for {stock_code}: {e}")
            return []


_sina_fetcher = SinaFinanceNewsFetcher()


# ── Main news fetcher ─────────────────────────────────────────────────────────

class NewsFetcher:
    RSS_URL = "https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"

    def fetch_news(
        self,
        ticker: str,
        max_items: int = 20,
        market: str = "unknown",
    ) -> List[NewsItem]:
        """
        Fetch recent news headlines for a ticker.
        A-shares: tries Sina Finance (Chinese) first, falls back to Yahoo.
        HK / BTC / other: uses Yahoo Finance RSS.
        """
        if market == "a_share":
            stock_code = ticker.split(".")[0]  # "600519.SS" → "600519"
            sina_items = _sina_fetcher.fetch(stock_code, max_items)
            if sina_items:
                return sina_items
            logger.info(f"Sina Finance empty for {ticker}, falling back to Yahoo RSS")

        return self._fetch_yahoo_rss(ticker, max_items)

    def _fetch_yahoo_rss(self, ticker: str, max_items: int) -> List[NewsItem]:
        url = self.RSS_URL.format(ticker=ticker)
        try:
            feed = feedparser.parse(url)
            items = []
            for entry in feed.entries[:max_items]:
                items.append(NewsItem(
                    title=entry.get("title", ""),
                    summary=entry.get("summary", ""),
                    link=entry.get("link", ""),
                    published=entry.get("published", ""),
                ))
            return items
        except Exception as e:
            logger.error(f"Yahoo Finance RSS fetch failed for {ticker}: {e}")
            return []

    def to_text_summary(
        self,
        ticker: str,
        max_items: int = 15,
        market: str = "unknown",
    ) -> str:
        """Format news as text for LLM context."""
        items = self.fetch_news(ticker, max_items, market=market)
        if not items:
            return f"暂无 {ticker} 的最新新闻 / No recent news found for {ticker}"

        source_label = "新浪财经（中文）" if market == "a_share" else "Yahoo Finance"
        lines = [f"# {ticker} 最新新闻（{source_label}，共 {len(items)} 条）\n"]
        for i, item in enumerate(items, 1):
            lines.append(f"## {i}. {item.title}")
            if item.published:
                lines.append(f"发布时间: {item.published}")
            if item.summary:
                summary = item.summary[:500] + "..." if len(item.summary) > 500 else item.summary
                lines.append(summary)
            lines.append(f"来源: {item.link}\n")

        return "\n".join(lines)


news_fetcher = NewsFetcher()
