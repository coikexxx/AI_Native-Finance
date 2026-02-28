"""Persistent application settings model (singleton row, id=1)."""
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from app.models.db import Base


class AppSettings(Base):
    __tablename__ = "app_settings"

    # Always a single row with id=1
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    api_key_override: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    max_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
