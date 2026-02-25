from sqlalchemy import String, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional
from app.models.db import Base
import uuid


def _uuid() -> str:
    return str(uuid.uuid4())


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    job_id: Mapped[str] = mapped_column(String, ForeignKey("analysis_jobs.id"), nullable=False, index=True)
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # filing | price_data | news | earnings_call | macro | company_info

    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_label: Mapped[str] = mapped_column(String(200), nullable=False)
    # e.g. "Apple 10-K 2024 p.42"

    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    data_snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    citation_key: Mapped[str] = mapped_column(String(10), nullable=False)
    # "[E1]", "[E2]", ...

    job: Mapped["AnalysisJob"] = relationship("AnalysisJob", back_populates="evidence_items")


# Import to avoid circular reference
from app.models.analysis import AnalysisJob  # noqa
