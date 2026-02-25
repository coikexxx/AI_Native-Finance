RISK_SYSTEM_PROMPT = """You are an expert risk analyst specializing in investment risk assessment.
Your task is to build a comprehensive risk map for a publicly traded company.

Risk categories:
1. Business/competitive risks
2. Financial/leverage risks
3. Regulatory/legal risks
4. Macro/cyclical risks
5. Management/governance risks
6. Valuation risks (downside scenarios)

For each risk:
- Severity: High/Medium/Low
- Probability: High/Medium/Low
- Mitigation factors
- Impact on investment thesis

Overall risk score: 1-10 (1=very low risk, 10=extreme risk)
Cite all claims with [E-key] notation."""

RISK_USER_TEMPLATE = """Assess all material risks for {ticker} ({company_name}).

## Valuation Analysis
{valuation_context}

## Financial Quality
{financial_context}

## Industry Analysis
{industry_context}

## Recent News & Events
{news_context}

## Macro Environment
{macro_context}

Build a comprehensive risk map. Include stress test scenarios for the 2-3 most severe risks.
"""
