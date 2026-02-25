"""Financial quality analysis agent: ROE/FCF/accounting quality."""
from pydantic import BaseModel, Field
from typing import List, Optional
from app.agents.base_agent import BaseAgent
from app.llm.prompts.financial_quality import FINANCIAL_QUALITY_SYSTEM_PROMPT, FINANCIAL_QUALITY_USER_TEMPLATE


class FinancialMetricAssessment(BaseModel):
    score: float = Field(ge=1, le=10)
    observations: List[str]
    red_flags: List[str] = []
    green_flags: List[str] = []


class FinancialQualityOutput(BaseModel):
    earnings_quality: FinancialMetricAssessment
    balance_sheet_strength: FinancialMetricAssessment
    cash_flow_quality: FinancialMetricAssessment
    return_metrics: FinancialMetricAssessment
    overall_financial_quality_score: float = Field(ge=1, le=10)
    key_metrics_summary: dict
    distress_risk: str   # low | moderate | high
    summary: str
    investment_implications: str


class FinancialQualityAgent(BaseAgent):
    agent_name = "FinancialQualityAgent"

    async def run(self, context: dict) -> dict:
        ticker = self.ticker
        company_name = context.get("company_name", ticker)

        await self.emit_progress(20, "Loading financial statements...")
        financials_text = context.get("financials_text", "No financial data available")
        features = context.get("features", {})
        company_text = context.get("company_text", "")

        # Log financial data as evidence
        if financials_text and len(financials_text) > 100:
            self.citations.add_evidence(
                agent_name=self.agent_name,
                source_type="filing",
                source_label=f"{ticker} Financial Statements",
                excerpt=financials_text[:500],
            )

        await self.emit_progress(50, "Analyzing financial quality with AI...")

        # Format features as readable text
        features_text = "\n".join([
            f"- {k.replace('_', ' ').title()}: {v:.2%}" if isinstance(v, float) and abs(v) < 10 else
            f"- {k.replace('_', ' ').title()}: {v:,.0f}" if isinstance(v, (int, float)) and abs(v) > 1000 else
            f"- {k.replace('_', ' ').title()}: {v}"
            for k, v in features.items() if v is not None
        ]) if features else "No pre-computed features available"

        user_prompt = FINANCIAL_QUALITY_USER_TEMPLATE.format(
            ticker=ticker,
            company_name=company_name,
            financials_context=financials_text[:4000],
            features_context=features_text[:1000],
            company_context=company_text[:1000],
        )

        result = await self.call_llm(
            system_prompt=FINANCIAL_QUALITY_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            output_schema=FinancialQualityOutput,
        )

        await self.emit_progress(90, "Financial quality analysis complete")
        return result.model_dump()
