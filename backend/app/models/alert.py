from sqlalchemy import String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, List
from app.models.db import Base
import uuid


def _uuid() -> str:
    return str(uuid.uuid4())


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    alert_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # price_above | price_below | earnings_date | re_analyze | custom

    target_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cron_expression: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    event_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_trigger_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    triggers: Mapped[List["AlertTrigger"]] = relationship(
        "AlertTrigger", back_populates="alert", lazy="selectin", cascade="all, delete-orphan"
    )


class AlertTrigger(Base):
    __tablename__ = "alert_triggers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    alert_id: Mapped[str] = mapped_column(String, ForeignKey("alerts.id"), nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    trigger_value: Mapped[str] = mapped_column(Text, nullable=False)
    action_taken: Mapped[str] = mapped_column(Text, nullable=False, default="")

    alert: Mapped["Alert"] = relationship("Alert", back_populates="triggers")
