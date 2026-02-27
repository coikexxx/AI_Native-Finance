from sqlalchemy import String, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
from app.models.db import Base
import uuid


def _uuid() -> str:
    return str(uuid.uuid4())


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_analysis_job_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Monitoring fields - populated by scheduled watchlist monitor jobs
    last_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_price_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_news_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
