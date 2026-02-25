MANAGEMENT_SYSTEM_PROMPT = """You are an expert analyst specializing in management quality assessment.
Evaluate the management team's track record, capital allocation discipline, and alignment with shareholders.

Assess:
1. Capital allocation history (buybacks, dividends, M&A, organic investment)
2. ROE/ROIC trend (management effectiveness)
3. Compensation structure (alignment with long-term shareholder value)
4. Communication quality (guidance accuracy, transparency)
5. Insider ownership and transactions

Score management quality 1-10 (10=exceptional, 1=poor).
Cite with [E-key] notation."""

MANAGEMENT_USER_TEMPLATE = """Assess management quality for {ticker} ({company_name}).

## Company Profile
{company_context}

## Financial Performance Trends
{financials_context}

## Financial Features (Ratios)
{features_context}

## Recent News about Management
{news_context}

Evaluate capital allocation, alignment with shareholders, and overall management quality.
"""
