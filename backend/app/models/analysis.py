from sqlalchemy import String, DateTime, JSON, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, List
from app.models.db import Base
import uuid


def _uuid() -> str:
    return str(uuid.uuid4())


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    # pending | running | complete | failed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    result: Mapped[Optional["AnalysisResult"]] = relationship(
        "AnalysisResult", back_populates="job", uselist=False, lazy="selectin"
    )
    evidence_items: Mapped[List["EvidenceItem"]] = relationship(
        "EvidenceItem", back_populates="job", lazy="selectin"
    )


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    job_id: Mapped[str] = mapped_column(String, ForeignKey("analysis_jobs.id"), nullable=False)

    # Agent output blobs (JSON)
    industry_analysis: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    business_model: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    moat_score: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    financial_quality: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    management_assessment: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    valuation: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    risk_assessment: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    thesis: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    monitoring_setup: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Aggregate outputs
    scorecard: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    decision: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    decision_rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    investment_memo_md: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dcf_assumptions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    scenario_outputs: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job: Mapped["AnalysisJob"] = relationship("AnalysisJob", back_populates="result")
