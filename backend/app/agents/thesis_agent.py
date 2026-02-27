"""Investment thesis synthesis agent."""
from pydantic import BaseModel, Field
from typing import List, Literal
from app.agents.base_agent import BaseAgent
from app.llm.prompts.thesis import THESIS_SYSTEM_PROMPT, THESIS_USER_TEMPLATE
from app.llm.prompts.market_context import get_system_snippet


class KeyVariable(BaseModel):
    variable_name: str
    description: str
    current_status: str
    bull_indicator: str
    bear_indicator: str


class ThesisOutput(BaseModel):
    executive_summary: str
    investment_thesis: str         # Bull case - why to own
    counter_thesis: str            # Bear case - key risks to thesis
    key_variables: List[KeyVariable]
    decision: Literal["Buy", "Hold", "Watch", "No"]
    decision_rationale: str
    investment_memo_md: str        # Full markdown memo with citations
    conviction_level: str          # High | Medium | Low
    time_horizon: str              # Short-term | Medium-term | Long-term


class ThesisAgent(BaseAgent):
    agent_name = "ThesisAgent"

    async def run(self, context: dict) -> dict:
        ticker = self.ticker
        company_name = context.get("company_name", ticker)
        market = context.get("market", "unknown")
        market_snippet = get_system_snippet(market)

        await self.emit_progress(20, "Synthesizing all research...")

        # Build scorecard
        fin_score = context.get("financial_quality", {}).get("overall_financial_quality_score", 5.0)
        moat_score = context.get("moat_score", {}).get("overall_moat_score", 5.0)
        val_score = context.get("valuation", {}).get("valuation_score", 5.0)
        risk_score = context.get("risk_assessment", {}).get("overall_risk_score", 5.0)
        # Invert risk score (high risk = lower overall score)
        risk_adjusted = 10 - risk_score + 1
        overall = (fin_score + moat_score + val_score + risk_adjusted) / 4

        scorecard_context = f"""Scorecard:
- Financial Quality: {fin_score:.1f}/10
- Moat Score: {moat_score:.1f}/10
- Valuation Attractiveness: {val_score:.1f}/10
- Risk Score (raw): {risk_score:.1f}/10 (lower risk = better)
- Overall: {overall:.1f}/10"""

        user_prompt = THESIS_USER_TEMPLATE.format(
            ticker=ticker,
            company_name=company_name,
            industry_context=str(context.get("industry_analysis", {}))[:1500],
            business_model_context=str(context.get("business_model", {}))[:1000],
            moat_context=str(context.get("moat_score", {}))[:1500],
            financial_quality_context=str(context.get("financial_quality", {}))[:1500],
            management_context=str(context.get("management_assessment", {}))[:1000],
            valuation_context=str(context.get("valuation", {}))[:1500],
            risk_context=str(context.get("risk_assessment", {}))[:1500],
            scorecard_context=scorecard_context,
        )

        await self.emit_progress(50, "Generating investment memo with AI...")

        system_prompt = market_snippet + "\n\n" + THESIS_SYSTEM_PROMPT if market_snippet else THESIS_SYSTEM_PROMPT
        result = await self.call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            output_schema=ThesisOutput,
            max_tokens=8192,
        )

        output = result.model_dump()
        output["scorecard"] = {
            "financial_quality_score": round(fin_score, 1),
            "moat_score": round(moat_score, 1),
            "valuation_score": round(val_score, 1),
            "risk_score": round(risk_score, 1),
            "overall_score": round(overall, 1),
        }

        await self.emit_progress(90, "Investment thesis complete")
        return output
