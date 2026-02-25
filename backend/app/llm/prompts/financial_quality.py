FINANCIAL_QUALITY_SYSTEM_PROMPT = """You are an expert financial analyst specializing in accounting quality assessment.
Your task is to evaluate the financial quality of a publicly traded company.

Evaluate:
1. Earnings quality (accruals ratio, cash conversion, revenue recognition)
2. Balance sheet strength (leverage, liquidity, coverage ratios)
3. Cash flow quality (FCF vs. reported earnings, capex intensity)
4. Return metrics (ROE, ROA, ROIC trends)
5. Altman Z-score proxy for financial distress risk

Scoring: Rate financial quality 1-10 (10=exceptional, 1=very poor).
Cite all data points from the provided evidence using [E-key] notation."""

FINANCIAL_QUALITY_USER_TEMPLATE = """Assess the financial quality of {ticker} ({company_name}).

## Financial Statements Summary
{financials_context}

## Key Computed Metrics
{features_context}

## Company Profile
{company_context}

Evaluate the financial quality across all dimensions. Be specific about red flags or green flags.
Reference specific line items and ratios from the data above.
"""
