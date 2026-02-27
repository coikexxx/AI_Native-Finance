"""Risk analysis agent: risk map, stress tests."""
from pydantic import BaseModel, Field
from typing import List
from app.agents.base_agent import BaseAgent
from app.llm.prompts.risk import RISK_SYSTEM_PROMPT, RISK_USER_TEMPLATE
from app.llm.prompts.market_context import get_system_snippet


class RiskItem(BaseModel):
    risk_name: str
    category: str    # business | financial | regulatory | macro | management | valuation
    severity: str    # High | Medium | Low
    probability: str  # High | Medium | Low
    description: str
    mitigation_factors: List[str] = []


class RiskOutput(BaseModel):
    risks: List[RiskItem]
    overall_risk_score: float = Field(ge=1, le=10)
    top_3_risks: List[str]
    stress_test_scenario: str
    stress_test_downside_pct: float
    risk_trend: str  # increasing | stable | decreasing
    summary: str


class RiskAgent(BaseAgent):
    agent_name = "RiskAgent"

    async def run(self, context: dict) -> dict:
        ticker = self.ticker
        company_name = context.get("company_name", ticker)
        market = context.get("market", "unknown")
        market_snippet = get_system_snippet(market)

        await self.emit_progress(30, "Mapping risk factors...")

        user_prompt = RISK_USER_TEMPLATE.format(
            ticker=ticker,
            company_name=company_name,
            valuation_context=str(context.get("valuation", {}))[:1500],
            financial_context=str(context.get("financial_quality", {}))[:1500],
            industry_context=str(context.get("industry_analysis", {}))[:1500],
            news_context=context.get("news_text", "")[:1500],
            macro_context=context.get("macro_text", "")[:800],
        )

        await self.emit_progress(60, "Stress-testing investment scenarios with AI...")

        system_prompt = market_snippet + "\n\n" + RISK_SYSTEM_PROMPT if market_snippet else RISK_SYSTEM_PROMPT
        result = await self.call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            output_schema=RiskOutput,
        )

        await self.emit_progress(90, "Risk assessment complete")
        return result.model_dump()
