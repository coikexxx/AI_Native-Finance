"""Management quality analysis agent."""
from pydantic import BaseModel, Field
from typing import List
from app.agents.base_agent import BaseAgent
from app.llm.prompts.management import MANAGEMENT_SYSTEM_PROMPT, MANAGEMENT_USER_TEMPLATE


class ManagementOutput(BaseModel):
    capital_allocation_quality: float = Field(ge=1, le=10)
    shareholder_alignment: float = Field(ge=1, le=10)
    track_record_score: float = Field(ge=1, le=10)
    communication_transparency: float = Field(ge=1, le=10)
    overall_management_score: float = Field(ge=1, le=10)
    notable_capital_allocation_decisions: List[str]
    red_flags: List[str] = []
    green_flags: List[str] = []
    management_assessment: str
    summary: str


class ManagementAgent(BaseAgent):
    agent_name = "ManagementAgent"

    async def run(self, context: dict) -> dict:
        ticker = self.ticker
        company_name = context.get("company_name", ticker)

        await self.emit_progress(30, "Assessing management track record...")

        features = context.get("features", {})
        features_text = "\n".join([
            f"- {k.replace('_', ' ').title()}: {v:.2%}" if isinstance(v, float) and abs(v) < 10 else
            f"- {k.replace('_', ' ').title()}: {v}"
            for k, v in features.items() if v is not None and not k.startswith("raw_")
        ]) if features else "No pre-computed features"

        user_prompt = MANAGEMENT_USER_TEMPLATE.format(
            ticker=ticker,
            company_name=company_name,
            company_context=context.get("company_text", "")[:2000],
            financials_context=context.get("financials_text", "")[:2000],
            features_context=features_text[:800],
            news_context=context.get("news_text", "")[:1500],
        )

        await self.emit_progress(60, "Evaluating capital allocation with AI...")

        result = await self.call_llm(
            system_prompt=MANAGEMENT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            output_schema=ManagementOutput,
        )

        await self.emit_progress(90, "Management assessment complete")
        return result.model_dump()
