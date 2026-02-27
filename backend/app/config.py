from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # LLM
    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-4-6"
    llm_max_tokens: int = 8192

    # Database
    database_url: str = f"sqlite+aiosqlite:///{BASE_DIR}/data/db/finance.db"

    # FRED API (optional)
    fred_api_key: str = ""

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True
    frontend_url: str = "http://localhost:5173"

    # Cache
    cache_ttl_seconds: int = 86400

    # Analysis
    max_concurrent_agents: int = 3
    analysis_timeout_seconds: int = 300
    ingestion_fetch_timeout_seconds: int = 25

    # SSE
    sse_queue_size: int = 200

    # ChromaDB path
    chroma_path: str = str(BASE_DIR / "data" / "chroma")

    # Raw data lake path
    raw_data_path: str = str(BASE_DIR / "data" / "raw")

    # Feature store (separate SQLite file to reduce lock contention)
    feature_store_path: str = str(BASE_DIR / "data" / "db" / "feature_store.db")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
