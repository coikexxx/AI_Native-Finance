"""Stock monitor API routes — price snapshots and news feed for watchlist stocks."""
import asyncio
import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import get_db
from app.models.watchlist import WatchlistItem

router = APIRouter(prefix="/api/v1/monitor", tags=["monitor"])
logger = logging.getLogger(__name__)


# ─── Response schemas ───────────────────────────────────────────────────────

class PriceSnapshot(BaseModel):
    ticker: str
    price: Optional[float] = None
    prev_close: Optional[float] = None
    change_pct: Optional[float] = None
    volume: Optional[int] = None
    avg_volume: Optional[int] = None
    volume_ratio: Optional[float] = None
    last_checked_at: Optional[datetime] = None
    market: Optional[str] = None
    currency: Optional[str] = None


class NewsItem(BaseModel):
    ticker: str
    title: str
    summary: str
    link: str
    published: str
    published_ts: Optional[float] = None   # epoch seconds for sorting
    significance: str = "medium"           # "high" | "medium" | "low"


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _parse_ts(published: str) -> Optional[float]:
    if not published:
        return None
    try:
        dt = parsedate_to_datetime(published)
        return dt.timestamp()
    except Exception:
        return None


def _significance(title: str, summary: str) -> str:
    from app.alerts.watchlist_monitor import _significance_score
    score = _significance_score(title, summary or "")
    if score >= 3:
        return "high"
    if score >= 1:
        return "medium"
    return "low"


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.get("/prices", response_model=List[PriceSnapshot])
async def get_watchlist_prices(db: AsyncSession = Depends(get_db)):
    """
    Return live price snapshots (price, % change, volume ratio) for all watchlist stocks.
    Fetches fresh data from yfinance in parallel.
    """
    result = await db.execute(select(WatchlistItem))
    items = result.scalars().all()

    if not items:
        return []

    from app.ingestion.market_data import market_data_fetcher

    async def fetch(item: WatchlistItem) -> PriceSnapshot:
        from app.ingestion.ticker_resolver import resolve_ticker
        try:
            ticker_info = resolve_ticker(item.ticker)
            market = ticker_info["market"]
            currency = ticker_info["currency"]
        except Exception:
            market = "unknown"
            currency = "$"
        try:
            detail = await asyncio.to_thread(
                market_data_fetcher.fetch_price_detail, item.ticker
            )
            return PriceSnapshot(
                ticker=item.ticker,
                price=detail.get("price"),
                prev_close=detail.get("prev_close"),
                change_pct=detail.get("change_pct"),
                volume=detail.get("volume"),
                avg_volume=detail.get("avg_volume"),
                volume_ratio=detail.get("volume_ratio"),
                last_checked_at=item.last_price_checked_at,
                market=market,
                currency=currency,
            )
        except Exception:
            return PriceSnapshot(ticker=item.ticker, market=market, currency=currency)

    snapshots = await asyncio.gather(*[fetch(item) for item in items])
    return list(snapshots)


@router.get("/news", response_model=List[NewsItem])
async def get_watchlist_news(
    max_per_ticker: int = 5,
    db: AsyncSession = Depends(get_db),
):
    """
    Return recent news articles for all watchlist stocks, sorted by publication time.
    Items are tagged with a significance level (high / medium / low).
    """
    result = await db.execute(select(WatchlistItem))
    items = result.scalars().all()

    if not items:
        return []

    from app.ingestion.news import news_fetcher

    async def fetch(item: WatchlistItem) -> List[NewsItem]:
        try:
            raw = await asyncio.to_thread(news_fetcher.fetch_news, item.ticker, max_per_ticker)
            out = []
            for n in raw:
                sig = _significance(n.title, n.summary or "")
                out.append(NewsItem(
                    ticker=item.ticker,
                    title=n.title,
                    summary=(n.summary or "")[:300],
                    link=n.link,
                    published=n.published,
                    published_ts=_parse_ts(n.published),
                    significance=sig,
                ))
            return out
        except Exception:
            return []

    results = await asyncio.gather(*[fetch(item) for item in items])
    all_news = [item for sublist in results for item in sublist]

    # Sort by publication time descending (newest first), unknowns last
    all_news.sort(key=lambda x: x.published_ts or 0, reverse=True)
    return all_news


@router.post("/check-now", status_code=202)
async def trigger_manual_check(db: AsyncSession = Depends(get_db)):
    """
    Manually trigger an immediate price-anomaly and news check for all watchlist stocks.
    Useful for testing — the results are sent via SSE as normal notifications.
    """
    from app.alerts.watchlist_monitor import watchlist_monitor

    async def _run():
        await watchlist_monitor.check_price_anomalies()
        await watchlist_monitor.check_news()

    asyncio.create_task(_run())
    return {"status": "check triggered", "message": "Monitoring check started, results via SSE"}
