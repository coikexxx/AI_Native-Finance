"""Watchlist routes."""
import asyncio
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime

from app.models.db import get_db
from app.models.watchlist import WatchlistItem

router = APIRouter(prefix="/api/v1/watchlist", tags=["watchlist"])


class WatchlistAddRequest(BaseModel):
    ticker: str
    notes: str = ""


class WatchlistItemResponse(BaseModel):
    id: str
    ticker: str
    added_at: datetime
    last_analysis_job_id: str | None = None
    notes: str | None = None
    current_price: float | None = None
    price_change_pct: float | None = None

    class Config:
        from_attributes = True


@router.get("", response_model=List[WatchlistItemResponse])
async def list_watchlist(db: AsyncSession = Depends(get_db)):
    stmt = select(WatchlistItem)
    result = await db.execute(stmt)
    items = result.scalars().all()

    # Enrich with live prices
    responses = []
    for item in items:
        resp = WatchlistItemResponse(
            id=item.id,
            ticker=item.ticker,
            added_at=item.added_at,
            last_analysis_job_id=item.last_analysis_job_id,
            notes=item.notes,
        )
        try:
            from app.ingestion.market_data import market_data_fetcher
            price = await asyncio.to_thread(market_data_fetcher.fetch_fast_price, item.ticker)
            resp.current_price = price
        except Exception:
            pass
        responses.append(resp)
    return responses


@router.post("", response_model=WatchlistItemResponse)
async def add_to_watchlist(
    payload: WatchlistAddRequest,
    db: AsyncSession = Depends(get_db),
):
    ticker = payload.ticker.strip().upper()
    # Check duplicate
    stmt = select(WatchlistItem).where(WatchlistItem.ticker == ticker)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        return WatchlistItemResponse(
            id=existing.id, ticker=existing.ticker, added_at=existing.added_at,
            last_analysis_job_id=existing.last_analysis_job_id, notes=existing.notes,
        )

    item = WatchlistItem(ticker=ticker, notes=payload.notes or None)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return WatchlistItemResponse(
        id=item.id, ticker=item.ticker, added_at=item.added_at, notes=item.notes,
    )


@router.delete("/{ticker}", status_code=204)
async def remove_from_watchlist(ticker: str, db: AsyncSession = Depends(get_db)):
    ticker = ticker.upper()
    stmt = select(WatchlistItem).where(WatchlistItem.ticker == ticker)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail=f"{ticker} not in watchlist")
    db.delete(item)
    await db.commit()
