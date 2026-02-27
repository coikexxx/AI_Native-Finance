from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import inspect, text
from app.config import settings
import os
import logging

logger = logging.getLogger(__name__)

# Ensure DB directory exists
os.makedirs(os.path.dirname(settings.database_url.replace("sqlite+aiosqlite:///", "")), exist_ok=True)

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def _migrate_watchlist_monitor_columns(conn) -> None:
    """Add monitoring columns to watchlist_items if they don't exist (SQLite ALTER TABLE)."""
    new_columns = [
        ("last_price", "REAL"),
        ("last_price_checked_at", "DATETIME"),
        ("last_news_checked_at", "DATETIME"),
    ]
    for col_name, col_type in new_columns:
        try:
            await conn.execute(
                text(f"ALTER TABLE watchlist_items ADD COLUMN {col_name} {col_type}")
            )
            logger.info(f"Migration: added column watchlist_items.{col_name}")
        except Exception:
            # Column already exists — SQLite raises OperationalError
            pass


async def init_db() -> None:
    """Create all tables on startup, then apply incremental migrations."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _migrate_watchlist_monitor_columns(conn)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
