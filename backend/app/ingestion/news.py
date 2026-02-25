"""News ingestion via Yahoo Finance RSS feeds."""
import feedparser
import httpx
from typing import List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NewsItem:
    def __init__(self, title: str, summary: str, link: str, published: str):
        self.title = title
        self.summary = summary
        self.link = link
        self.published = published


class NewsFetcher:
    RSS_URL = "https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"

    def fetch_news(self, ticker: str, max_items: int = 20) -> List[NewsItem]:
        """Fetch recent news headlines for a ticker via RSS."""
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
            logger.error(f"Error fetching news for {ticker}: {e}")
            return []

    def to_text_summary(self, ticker: str, max_items: int = 15) -> str:
        """Format news as text for LLM context."""
        items = self.fetch_news(ticker, max_items)
        if not items:
            return f"No recent news found for {ticker}"

        lines = [f"# Recent News for {ticker} ({len(items)} articles)\n"]
        for i, item in enumerate(items, 1):
            lines.append(f"## {i}. {item.title}")
            lines.append(f"Published: {item.published}")
            if item.summary:
                # Truncate long summaries
                summary = item.summary[:500] + "..." if len(item.summary) > 500 else item.summary
                lines.append(summary)
            lines.append(f"Source: {item.link}\n")

        return "\n".join(lines)


news_fetcher = NewsFetcher()
