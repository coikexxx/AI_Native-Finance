"""Valuation agent: DCF, owner earnings, comparable multiples."""
from pydantic import BaseModel, Field
from typing import List, Optional
from app.agents.base_agent import BaseAgent
from app.llm.prompts.valuation import VALUATION_SYSTEM_PROMPT, VALUATION_USER_TEMPLATE
from app.tools.financial_model import DCFInputs, DCFModel
from app.tools.monte_carlo import MonteCarloSimulator


class ValuationOutput(BaseModel):
    dcf_growth_rate_yr1_5_pct: float
    dcf_growth_rate_yr6_10_pct: float
    dcf_terminal_growth_rate_pct: float
    dcf_wacc_pct: float
    dcf_intrinsic_value: float
    dcf_current_price: float
    dcf_margin_of_safety_pct: float
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    ev_ebitda: Optional[float] = None
    pb_ratio: Optional[float] = None
    valuation_score: float = Field(ge=1, le=10)
    valuation_verdict: str  # attractive | fair | stretched | expensive
    bull_case_value: Optional[float] = None
    base_case_value: Optional[float] = None
    bear_case_value: Optional[float] = None
    key_valuation_drivers: List[str]
    summary: str


class ValuationAgent(BaseAgent):
    agent_name = "ValuationAgent"

    async def run(self, context: dict) -> dict:
        ticker = self.ticker
        company_name = context.get("company_name", ticker)

        await self.emit_progress(20, "Building DCF model...")

        features = context.get("features", {})
        price_features = context.get("price_features", {})
        current_price = price_features.get("current_price") or context.get("current_price", 0)
        company_info = context.get("company_info", {})

        # Build DCF if we have FCF data
        dcf_context = "DCF data not available"
        dcf_output = None
        scenario_outputs = []

        fcf = features.get("free_cash_flow")
        shares = company_info.get("sharesOutstanding")

        if fcf and shares and shares > 0 and current_price > 0:
            try:
                dcf_model = DCFModel()
                mc = MonteCarloSimulator()

                # Estimate growth from historical data
                rev_growth = features.get("revenue_growth_yoy", 0.08)
                fcf_growth = max(min(rev_growth * 1.1, 0.40), -0.10)

                total_debt = company_info.get("totalDebt") or 0
                cash = company_info.get("totalCash") or 0
                net_cash = cash - total_debt

                inputs = DCFInputs(
                    current_fcf=fcf,
                    growth_rate_yr1_5=fcf_growth,
                    growth_rate_yr6_10=max(fcf_growth * 0.6, 0.03),
                    terminal_growth_rate=0.03,
                    wacc=0.09,
                    shares_outstanding=shares,
                    net_cash=net_cash,
                )

                dcf_output = dcf_model.calculate(inputs, current_price)
                scenarios = mc.run_scenarios(inputs, current_price)

                dcf_context = f"""DCF Model Results:
- Intrinsic Value: ${dcf_output.intrinsic_value_per_share:.2f}
- Current Price: ${current_price:.2f}
- Margin of Safety: {dcf_output.margin_of_safety_pct:.1f}%
- Assumptions: Growth Y1-5={fcf_growth*100:.1f}%, WACC=9%, Terminal Growth=3%

Scenarios:
{chr(10).join([f'- {s.scenario_name}: ${s.intrinsic_value:.2f} ({s.return_pct:+.1f}%)' for s in scenarios])}"""

                scenario_outputs = [
                    {"scenario_name": s.scenario_name, "probability_pct": s.probability_pct,
                     "intrinsic_value": s.intrinsic_value, "return_pct": s.return_pct}
                    for s in scenarios
                ]

                self.citations.add_evidence(
                    agent_name=self.agent_name,
                    source_type="price_data",
                    source_label=f"{ticker} DCF Model",
                    excerpt=dcf_context,
                    data_snapshot={"dcf": dcf_output.__dict__, "features": features},
                )
            except Exception as e:
                dcf_context = f"DCF calculation failed: {e}"

        await self.emit_progress(60, "Running valuation assessment with AI...")

        market_context = f"""
Current Price: ${current_price:.2f}
Market Cap: ${company_info.get('marketCap', 0):,.0f}
P/E (trailing): {company_info.get('trailingPE', 'N/A')}
P/E (forward): {company_info.get('forwardPE', 'N/A')}
EV/EBITDA: {company_info.get('enterpriseToEbitda', 'N/A')}
P/B: {company_info.get('priceToBook', 'N/A')}
"""

        user_prompt = VALUATION_USER_TEMPLATE.format(
            ticker=ticker,
            company_name=company_name,
            current_price=f"${current_price:.2f}" if current_price else "N/A",
            features_context="\n".join([f"- {k}: {v}" for k, v in features.items() if v is not None])[:1500],
            financials_context=context.get("financials_text", "")[:2000],
            moat_context=str(context.get("moat_score", {}))[:1000],
            dcf_context=dcf_context,
            market_context=market_context,
        )

        result = await self.call_llm(
            system_prompt=VALUATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            output_schema=ValuationOutput,
        )

        output = result.model_dump()
        output["scenario_outputs"] = scenario_outputs
        if dcf_output:
            output["dcf_sensitivity_table"] = dcf_output.sensitivity_table

        await self.emit_progress(90, "Valuation analysis complete")
        return output
