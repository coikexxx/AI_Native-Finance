"""Settings API routes — read/write model configuration."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import get_db
from app.services.settings_service import get_effective_settings, save_settings

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])
logger = logging.getLogger(__name__)


# ─── Schemas ──────────────────────────────────────────────────────────────────

class SettingsRead(BaseModel):
    model_name: str
    api_key_set: bool   # Never return the actual key
    max_tokens: int


class SettingsWrite(BaseModel):
    model_name: str
    api_key: str = ""   # empty = keep existing key
    max_tokens: int = 8192


class TestConnectionResult(BaseModel):
    ok: bool
    model: Optional[str] = None
    error: Optional[str] = None


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("", response_model=SettingsRead)
async def get_settings(db: AsyncSession = Depends(get_db)):
    """Return effective LLM settings (api key is never returned, only api_key_set bool)."""
    from app.models.settings import AppSettings
    from sqlalchemy import select

    effective = await get_effective_settings(db)

    # Check if an override key is stored in DB
    result = await db.execute(select(AppSettings).where(AppSettings.id == 1))
    row = result.scalar_one_or_none()
    api_key_set = bool(row and row.api_key_override)

    return SettingsRead(
        model_name=effective.model_name,
        api_key_set=api_key_set,
        max_tokens=effective.max_tokens,
    )


@router.put("", response_model=SettingsRead)
async def update_settings(payload: SettingsWrite, db: AsyncSession = Depends(get_db)):
    """
    Save model configuration to DB.
    - api_key="" means keep the existing override (or env var fallback)
    - api_key="sk-..." sets a new override key
    """
    await save_settings(
        db,
        model_name=payload.model_name,
        api_key_override=payload.api_key if payload.api_key else None,
        max_tokens=payload.max_tokens,
    )

    # Re-read to confirm and return the saved state
    return await get_settings(db)


@router.post("/test-connection", response_model=TestConnectionResult)
async def test_connection(db: AsyncSession = Depends(get_db)):
    """
    Make a minimal Anthropic API call to verify the current credentials.
    Returns ok=True with model name on success, ok=False with error message on failure.
    """
    try:
        effective = await get_effective_settings(db)
        import anthropic
        client = anthropic.Anthropic(api_key=effective.api_key)
        message = client.messages.create(
            model=effective.model_name,
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}],
        )
        return TestConnectionResult(ok=True, model=effective.model_name)
    except Exception as e:
        logger.warning(f"Connection test failed: {e}")
        return TestConnectionResult(ok=False, error=str(e))
