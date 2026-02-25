"""Industry analysis agent: Porter's 5 Forces, competitive dynamics."""
from pydantic import BaseModel, Field
from typing import List, Optional
from app.agents.base_agent import BaseAgent
from app.llm.prompts.industry import INDUSTRY_SYSTEM_PROMPT, INDUSTRY_USER_TEMPLATE


class ForceAnalysis(BaseModel):
    score: float = Field(ge=1, le=10)
    summary: str
    key_observations: List[str]


class IndustryAnalysisOutput(BaseModel):
    competitive_rivalry: ForceAnalysis
    threat_of_new_entrants: ForceAnalysis
    bargaining_power_suppliers: ForceAnalysis
    bargaining_power_buyers: ForceAnalysis
    threat_of_substitutes: ForceAnalysis
    industry_lifecycle_stage: str  # growth | mature | decline | cyclical
    cyclicality: str               # high | moderate | low
    key_trends: List[str]
    overall_industry_attractiveness: float = Field(ge=1, le=10)
    summary: str


class IndustryAgent(BaseAgent):
    agent_name = "IndustryAgent"

    async def run(self, context: dict) -> dict:
        ticker = self.ticker
        company_name = context.get("company_name", ticker)

        await self.emit_progress(20, "Retrieving competitive context...")
        news_context = context.get("news_text", "")
        company_context = context.get("company_text", "")
        macro_context = context.get("macro_text", "")
        kg_context = context.get("kg_text", "")

        # Add evidence
        if news_context:
            self.citations.add_evidence(
                agent_name=self.agent_name,
                source_type="news",
                source_label=f"{ticker} Recent News",
                excerpt=news_context[:500],
            )
        if company_context:
            self.citations.add_evidence(
                agent_name=self.agent_name,
                source_type="company_info",
                source_label=f"{ticker} Company Profile",
                excerpt=company_context[:500],
            )

        await self.emit_progress(50, "Analyzing industry structure with AI...")

        user_prompt = INDUSTRY_USER_TEMPLATE.format(
            ticker=ticker,
            company_name=company_name,
            company_context=company_context[:3000],
            news_context=news_context[:2000],
            macro_context=macro_context[:1000],
            kg_context=kg_context[:500],
        )

        result = await self.call_llm(
            system_prompt=INDUSTRY_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            output_schema=IndustryAnalysisOutput,
        )

        await self.emit_progress(90, "Industry analysis complete")
        return result.model_dump()
