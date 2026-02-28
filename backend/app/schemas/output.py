from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Any, Dict
from datetime import datetime


class Scorecard(BaseModel):
    financial_quality_score: float = Field(ge=0, le=10)
    moat_score: float = Field(ge=0, le=10)
    valuation_score: float = Field(ge=0, le=10)
    risk_score: float = Field(ge=0, le=10)
    overall_score: float = Field(ge=0, le=10)


class DCFAssumptions(BaseModel):
    revenue_growth_rate_pct: float
    fcf_margin_pct: float
    terminal_growth_rate_pct: float
    wacc_pct: float
    projection_years: int = 10
    intrinsic_value_per_share: float
    current_price: float
    margin_of_safety_pct: float


class ScenarioResult(BaseModel):
    scenario_name: str  # Bull | Base | Bear
    probability_pct: float
    intrinsic_value: float
    return_pct: float


class EvidenceReference(BaseModel):
    citation_key: str
    agent_name: str
    source_label: str
    source_type: str
    excerpt: str
    source_url: Optional[str] = None


class InvestmentMemo(BaseModel):
    ticker: str
    company_name: str
    analysis_date: str
    decision: Literal["Buy", "Hold", "Watch", "No"]
    decision_rationale: str
    scorecard: Scorecard
    memo_markdown: str
    evidence_pack: List[EvidenceReference] = []
    dcf_assumptions: Optional[DCFAssumptions] = None
    scenario_outputs: List[ScenarioResult] = []


class AgentStatus(BaseModel):
    agent_name: str
    status: Literal["pending", "running", "complete", "failed"]
    progress_pct: int = 0
    current_task: Optional[str] = None
    duration_ms: Optional[int] = None


class AnalysisStreamEvent(BaseModel):
    event_type: Literal[
        "agent_start", "agent_progress", "agent_complete", "agent_error",
        "phase_start", "memo_chunk", "complete", "error"
    ]
    agent_name: Optional[str] = None
    payload: Dict[str, Any] = {}


class AnalysisJobResponse(BaseModel):
    job_id: str
    ticker: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    model_used: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0


class AnalysisResultResponse(BaseModel):
    job_id: str
    ticker: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    scorecard: Optional[Scorecard] = None
    decision: Optional[str] = None
    decision_rationale: Optional[str] = None
    investment_memo_md: Optional[str] = None
    dcf_assumptions: Optional[DCFAssumptions] = None
    scenario_outputs: Optional[List[ScenarioResult]] = None
    evidence_items: Optional[List[EvidenceReference]] = None
    model_used: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
