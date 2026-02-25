"""Monitoring agent: defines KPIs and tracking metrics."""
from pydantic import BaseModel, Field
from typing import List, Optional
from app.agents.base_agent import BaseAgent
from app.llm.prompts.monitoring import MONITORING_SYSTEM_PROMPT, MONITORING_USER_TEMPLATE


class KPIDefinition(BaseModel):
    kpi_name: str
    description: str
    current_value: Optional[str] = None
    bull_threshold: str
    bear_threshold: str
    reporting_cadence: str  # quarterly | annual | continuous | event_driven


class MonitoringOutput(BaseModel):
    kpis: List[KPIDefinition]
    thesis_confirmation_signals: List[str]
    thesis_invalidation_signals: List[str]
    recommended_review_frequency: str
    next_catalyst_date: Optional[str] = None
    summary: str


class MonitoringAgent(BaseAgent):
    agent_name = "MonitoringAgent"

    async def run(self, context: dict) -> dict:
        ticker = self.ticker
        company_name = context.get("company_name", ticker)

        await self.emit_progress(30, "Defining monitoring framework...")

        features = context.get("features", {})
        features_text = "\n".join([f"- {k}: {v}" for k, v in features.items()
                                    if v is not None and not k.startswith("raw_")])[:800]

        user_prompt = MONITORING_USER_TEMPLATE.format(
            ticker=ticker,
            company_name=company_name,
            thesis_context=str(context.get("thesis", {}))[:2000],
            features_context=features_text,
            risk_context=str(context.get("risk_assessment", {}))[:1000],
        )

        await self.emit_progress(60, "Setting up monitoring framework with AI...")

        result = await self.call_llm(
            system_prompt=MONITORING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            output_schema=MonitoringOutput,
        )

        await self.emit_progress(90, "Monitoring setup complete")
        return result.model_dump()
