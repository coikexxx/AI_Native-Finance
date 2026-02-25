"""Economic moat analysis agent."""
from pydantic import BaseModel, Field
from typing import List
from app.agents.base_agent import BaseAgent
from app.llm.prompts.moat import MOAT_SYSTEM_PROMPT, MOAT_USER_TEMPLATE


class MoatSourceScore(BaseModel):
    score: float = Field(ge=0, le=10)
    evidence: str
    key_supporting_facts: List[str] = []


class MoatOutput(BaseModel):
    network_effects: MoatSourceScore
    switching_costs: MoatSourceScore
    cost_advantages: MoatSourceScore
    intangible_assets: MoatSourceScore
    efficient_scale: MoatSourceScore
    moat_classification: str      # None | Narrow | Wide
    moat_durability: float = Field(ge=1, le=10)
    overall_moat_score: float = Field(ge=1, le=10)
    moat_trend: str              # strengthening | stable | weakening
    key_moat_evidence: List[str]
    moat_vulnerabilities: List[str]
    summary: str


class MoatAgent(BaseAgent):
    agent_name = "MoatAgent"

    async def run(self, context: dict) -> dict:
        ticker = self.ticker
        company_name = context.get("company_name", ticker)

        await self.emit_progress(30, "Evaluating moat sources...")

        user_prompt = MOAT_USER_TEMPLATE.format(
            ticker=ticker,
            company_name=company_name,
            industry_context=str(context.get("industry_analysis", {}))[:2000],
            business_model_context=str(context.get("business_model", {}))[:1500],
            financial_context=str(context.get("financial_quality", {}))[:1500],
            company_context=context.get("company_text", "")[:1000],
        )

        await self.emit_progress(60, "Quantifying economic moat with AI...")

        result = await self.call_llm(
            system_prompt=MOAT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            output_schema=MoatOutput,
        )

        await self.emit_progress(90, "Moat analysis complete")
        return result.model_dump()
