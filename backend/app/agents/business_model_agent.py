"""Business model analysis agent: unit economics, revenue model."""
from pydantic import BaseModel, Field
from typing import List, Optional
from app.agents.base_agent import BaseAgent
from app.llm.prompts.business_model import BUSINESS_MODEL_SYSTEM_PROMPT, BUSINESS_MODEL_USER_TEMPLATE


class BusinessModelOutput(BaseModel):
    revenue_model_type: str        # subscription | transactional | product | service | platform | hybrid
    revenue_concentration_risk: str  # high | moderate | low
    pricing_power: str             # strong | moderate | weak
    operating_leverage: str        # high | moderate | low
    capital_intensity: str         # high | moderate | low
    unit_economics_quality: str    # excellent | good | fair | poor | not_applicable
    recurring_revenue_pct: Optional[float] = None
    key_revenue_drivers: List[str]
    business_model_score: float = Field(ge=1, le=10)
    sustainability_assessment: str
    summary: str


class BusinessModelAgent(BaseAgent):
    agent_name = "BusinessModelAgent"

    async def run(self, context: dict) -> dict:
        ticker = self.ticker
        company_name = context.get("company_name", ticker)

        await self.emit_progress(30, "Analyzing business model structure...")

        user_prompt = BUSINESS_MODEL_USER_TEMPLATE.format(
            ticker=ticker,
            company_name=company_name,
            company_context=context.get("company_text", "")[:3000],
            financials_context=context.get("financials_text", "")[:2000],
            industry_context=str(context.get("industry_analysis", {}))[:1000],
        )

        await self.emit_progress(60, "Assessing unit economics with AI...")

        result = await self.call_llm(
            system_prompt=BUSINESS_MODEL_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            output_schema=BusinessModelOutput,
        )

        await self.emit_progress(90, "Business model analysis complete")
        return result.model_dump()
