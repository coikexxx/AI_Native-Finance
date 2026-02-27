"""Watchlist monitoring: price anomaly detection and news/sentiment alerts."""
import asyncio
import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Price change threshold to trigger an anomaly alert (percent)
PRICE_ANOMALY_THRESHOLD = 2.0

# Volume spike threshold (ratio to 3-month average)
VOLUME_SPIKE_THRESHOLD = 2.0

# Keywords indicating high-significance news — checked against title + summary
_HIGH_PRIORITY_KEYWORDS = [
    # Earnings / financials
    "earnings", "revenue", "profit", "loss", "beat", "miss", "guidance",
    "forecast", "outlook", "sales", "margin",
    # Corporate actions
    "merger", "acquisition", "buyout", "takeover", "deal", "spinoff",
    "dividend", "buyback", "split", "ipo",
    # Regulatory / legal
    "fda", "approval", "approved", "rejected", "recall", "warning letter",
    "sec", "investigation", "fraud", "lawsuit", "settlement", "fine",
    "bankruptcy", "default", "restructuring", "chapter 11",
    # Analyst actions
    "downgrade", "upgrade", "price target", "overweight", "underweight",
    "outperform", "underperform", "buy", "sell", "hold",
    # Executive / org
    "ceo", "cfo", "coo", "resign", "appoint", "fired", "layoff", "layoffs",
    # Product / operations
    "patent", "product launch", "recall", "supply chain",
    # Chinese keywords — A股/港股
    "盈利", "利润", "营收", "增长", "下滑", "亏损",
    "证监会", "监管", "处罚", "立案", "调查",
    "并购", "重组", "分红", "回购", "增发", "配股",
    "停牌", "复牌", "退市", "上市",
    "减持", "增持", "解禁",
    "业绩预告", "业绩快报", "年报", "半年报", "季报",
    "降息", "加息", "央行", "利好", "利空",
]


def _parse_pub_time(published: str) -> Optional[datetime]:
    """Parse RFC 2822 publication time to UTC-aware datetime."""
    if not published:
        return None
    try:
        dt = parsedate_to_datetime(published)
        # Ensure UTC-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _significance_score(title: str, summary: str) -> int:
    """Return how many high-priority keywords appear in the text (0 = not significant)."""
    combined = (title + " " + summary).lower()
    return sum(1 for kw in _HIGH_PRIORITY_KEYWORDS if kw in combined)


class WatchlistMonitor:
    """Scheduled jobs for watchlist price anomaly and news monitoring."""

    async def check_price_anomalies(self) -> None:
        """
        Check every watchlist stock for unusual price movement.
        Fires a `watchlist_price_anomaly` SSE notification when >= PRICE_ANOMALY_THRESHOLD %.
        Also checks for volume spikes (>= VOLUME_SPIKE_THRESHOLD × avg).
        """
        from app.models.db import AsyncSessionLocal
        from app.models.watchlist import WatchlistItem
        from app.ingestion.market_data import market_data_fetcher
        from app.core.sse_manager import sse_manager
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(WatchlistItem))
            items = result.scalars().all()

            if not items:
                return

            for item in items:
                try:
                    from app.ingestion.ticker_resolver import resolve_ticker
                    try:
                        ticker_info = resolve_ticker(item.ticker)
                        currency = ticker_info["currency"]
                    except Exception:
                        currency = "$"

                    detail = await asyncio.to_thread(
                        market_data_fetcher.fetch_price_detail, item.ticker
                    )
                    price = detail.get("price")
                    change_pct = detail.get("change_pct")
                    volume_ratio = detail.get("volume_ratio")

                    if price is None:
                        continue

                    # Detect price anomaly
                    if change_pct is not None and abs(change_pct) >= PRICE_ANOMALY_THRESHOLD:
                        direction = "上涨" if change_pct > 0 else "下跌"
                        sign = "+" if change_pct > 0 else ""
                        msg = (
                            f"{item.ticker} 价格{direction} {sign}{change_pct:.1f}%，"
                            f"当前价格 {currency}{price:.2f}"
                        )
                        await sse_manager.push_notification({
                            "event_type": "watchlist_price_anomaly",
                            "payload": {
                                "ticker": item.ticker,
                                "message": msg,
                                "change_pct": change_pct,
                                "price": price,
                                "prev_close": detail.get("prev_close"),
                                "volume_ratio": volume_ratio,
                            },
                        })
                        logger.info(f"Price anomaly alert: {msg}")

                    # Detect volume spike (independent of price anomaly)
                    elif (
                        volume_ratio is not None
                        and volume_ratio >= VOLUME_SPIKE_THRESHOLD
                        and price is not None
                    ):
                        msg = (
                            f"{item.ticker} 成交量异常放大 {volume_ratio:.1f}x 均值，"
                            f"当前价格 {currency}{price:.2f}"
                        )
                        await sse_manager.push_notification({
                            "event_type": "watchlist_price_anomaly",
                            "payload": {
                                "ticker": item.ticker,
                                "message": msg,
                                "change_pct": change_pct,
                                "price": price,
                                "volume_ratio": volume_ratio,
                                "anomaly_type": "volume_spike",
                            },
                        })
                        logger.info(f"Volume spike alert: {msg}")

                    # Update cached price state
                    item.last_price = price
                    item.last_price_checked_at = datetime.utcnow()

                except Exception as exc:
                    logger.warning(f"Price anomaly check failed for {item.ticker}: {exc}")

            await db.commit()

    async def check_news(self) -> None:
        """
        Check every watchlist stock for significant new news articles.
        Only reports news published after the last check time.
        Fires a `watchlist_news_alert` SSE notification for each significant item.
        """
        from app.models.db import AsyncSessionLocal
        from app.models.watchlist import WatchlistItem
        from app.ingestion.news import news_fetcher
        from app.core.sse_manager import sse_manager
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(WatchlistItem))
            items = result.scalars().all()

            if not items:
                return

            for item in items:
                try:
                    news_items = await asyncio.to_thread(
                        news_fetcher.fetch_news, item.ticker, 15
                    )
                    if not news_items:
                        item.last_news_checked_at = datetime.utcnow()
                        continue

                    # Determine cutoff: last check time (UTC-aware)
                    cutoff: Optional[datetime] = None
                    if item.last_news_checked_at:
                        cutoff = item.last_news_checked_at.replace(tzinfo=timezone.utc)

                    for news in news_items:
                        pub_time = _parse_pub_time(news.published)

                        # Skip old news on subsequent runs
                        if cutoff and pub_time and pub_time <= cutoff:
                            continue

                        score = _significance_score(news.title, news.summary or "")
                        if score == 0:
                            continue

                        significance = "high" if score >= 3 else "medium"
                        headline = news.title[:100] + ("…" if len(news.title) > 100 else "")
                        msg = f"{item.ticker} 重要新闻: {headline}"

                        await sse_manager.push_notification({
                            "event_type": "watchlist_news_alert",
                            "payload": {
                                "ticker": item.ticker,
                                "message": msg,
                                "headline": news.title,
                                "summary": (news.summary or "")[:300],
                                "link": news.link,
                                "published": news.published,
                                "significance": significance,
                                "score": score,
                            },
                        })
                        logger.info(f"News alert [{significance}]: {msg}")

                    item.last_news_checked_at = datetime.utcnow()

                except Exception as exc:
                    logger.warning(f"News check failed for {item.ticker}: {exc}")

            await db.commit()


watchlist_monitor = WatchlistMonitor()
