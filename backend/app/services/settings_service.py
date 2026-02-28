"""Settings service — DB queries with env-var fallback."""
from dataclasses import dataclass
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings as env_settings


@dataclass
class EffectiveSettings:
    model_name: str
    api_key: str
    max_tokens: int


async def get_effective_settings(db_session: AsyncSession) -> EffectiveSettings:
    """Return effective LLM settings: DB override takes precedence over env vars."""
    from app.models.settings import AppSettings

    result = await db_session.execute(
        select(AppSettings).where(AppSettings.id == 1)
    )
    row = result.scalar_one_or_none()

    return EffectiveSettings(
        model_name=(row.model_name if row and row.model_name else None)
                   or env_settings.llm_model,
        api_key=(row.api_key_override if row and row.api_key_override else None)
                or env_settings.anthropic_api_key,
        max_tokens=(row.max_tokens if row and row.max_tokens else None)
                   or env_settings.llm_max_tokens,
    )


async def save_settings(
    db_session: AsyncSession,
    model_name: Optional[str],
    api_key_override: Optional[str],
    max_tokens: Optional[int],
) -> None:
    """Upsert singleton settings row (id=1). Empty string api_key_override clears override."""
    from app.models.settings import AppSettings

    result = await db_session.execute(
        select(AppSettings).where(AppSettings.id == 1)
    )
    row = result.scalar_one_or_none()

    if row is None:
        row = AppSettings(id=1)
        db_session.add(row)

    if model_name is not None:
        row.model_name = model_name or None
    if api_key_override is not None:
        # Empty string means "clear the override, fall back to env var"
        row.api_key_override = api_key_override if api_key_override else None
    if max_tokens is not None:
        row.max_tokens = max_tokens

    await db_session.commit()
