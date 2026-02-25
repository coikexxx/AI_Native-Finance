"""Local filesystem raw data lake."""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Any, Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class ObjectStore:
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or settings.raw_data_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _path(self, ticker: str, source_type: str) -> Path:
        ticker_dir = self.base_path / ticker.upper()
        ticker_dir.mkdir(parents=True, exist_ok=True)
        return ticker_dir / f"{source_type}.json"

    def save(self, ticker: str, source_type: str, data: Any) -> str:
        """Save raw data to filesystem. Returns file path."""
        path = self._path(ticker, source_type)
        payload = {
            "ticker": ticker,
            "source_type": source_type,
            "saved_at": datetime.utcnow().isoformat(),
            "data": data,
        }
        try:
            # Convert DataFrames to JSON-serializable format
            if hasattr(data, "to_dict"):
                payload["data"] = data.to_dict()
            path.write_text(json.dumps(payload, default=str, ensure_ascii=False), encoding="utf-8")
            return str(path)
        except Exception as e:
            logger.error(f"Error saving {source_type} for {ticker}: {e}")
            return ""

    def load(self, ticker: str, source_type: str) -> Optional[dict]:
        """Load raw data from filesystem."""
        path = self._path(ticker, source_type)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return payload.get("data")
        except Exception as e:
            logger.error(f"Error loading {source_type} for {ticker}: {e}")
            return None

    def exists(self, ticker: str, source_type: str, max_age_seconds: int = 86400) -> bool:
        """Check if data exists and is fresh enough."""
        path = self._path(ticker, source_type)
        if not path.exists():
            return False
        age = datetime.utcnow().timestamp() - path.stat().st_mtime
        return age < max_age_seconds


object_store = ObjectStore()
