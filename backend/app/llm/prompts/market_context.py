"""
Market-specific context snippets injected into LLM system/user prompts.

Each value is a self-contained paragraph that can be prepended to any
agent's system prompt or user prompt to ground the LLM in the correct
market, regulatory environment, currency, and analytical framework.
"""

# Injected into the SYSTEM prompt of every agent
MARKET_SYSTEM_SNIPPETS: dict[str, str] = {
    "a_share": (
        "【A股市场背景】本次分析对象为在中国上交所（SSE）或深交所（SZSE）上市的A股。"
        "货币单位：人民币（CNY / ¥）。"
        "监管机构：中国证监会（CSRC），信息披露平台为巨潮资讯（cninfo.com.cn）。"
        "市场特点：每日涨跌停板限制（主板±10%，科创板/创业板±20%）；"
        "北向资金（陆股通）和两融余额是重要情绪指标；"
        "A股流动性受假期、IPO节奏和宏观政策影响较大。"
        "估值分析时请用人民币计价，并结合A股估值中枢（历史PE/PB区间）进行判断。"
    ),
    "hk": (
        "【港股市场背景】本次分析对象为在香港联合交易所（HKEX）上市的港股。"
        "货币单位：港元（HKD / HK$）。"
        "监管机构：香港证监会（SFC），信息披露通过港交所披露易（HKEX e-Disclosure）。"
        "港元与美元挂钩（联系汇率制度，约7.75–7.85 HKD/USD）。"
        "南向资金（港股通）是重要边际资金来源；"
        "港股流动性通常弱于A股，折让（discount）较为普遍。"
        "如为H+A双重上市股票，需关注AH溢价/折价情况。"
    ),
    "crypto": (
        "【加密货币分析框架】本次分析对象为比特币（Bitcoin / BTC），属于去中心化数字资产。"
        "传统股票分析框架（P/E比率、财务报表、DCF现金流折现）不适用。"
        "请使用以下加密货币专属框架进行分析："
        "1. 网络基本面：链上活跃地址数、交易量、算力（Hash Rate）、闪电网络容量；"
        "2. 供需模型：库存流量比（Stock-to-Flow / S2F）、减半周期影响；"
        "3. 估值指标：MVRV比率（市值/已实现市值）、NVT比率（市值/链上交易量）；"
        "4. 市场周期：牛熊市阶段判断、恐惧贪婪指数、鲸鱼持仓变化；"
        "5. 竞争格局：BTC市值占比（Dominance）、以太坊及其他主流链的相对表现；"
        "6. 监管风险：各主要经济体的加密货币政策动向（美国SEC、欧盟MiCA、中国监管）。"
        "所有估值结论须基于加密货币行业逻辑，避免套用传统股票框架。"
    ),
}

# Injected into the USER prompt of relevant agents (more concise)
MARKET_USER_SNIPPETS: dict[str, str] = {
    "a_share": "注：本标的为A股，货币为人民币（¥），请在分析中使用A股行业分类和估值标准。",
    "hk":      "注：本标的为港股，货币为港元（HK$），请在分析中考虑港股市场特有风险和估值折让。",
    "crypto":  "注：本标的为比特币（BTC），无传统财务报表，请使用加密货币专属分析框架。",
}


def get_system_snippet(market: str) -> str:
    """Return the market-specific system prompt snippet, empty string if unknown."""
    return MARKET_SYSTEM_SNIPPETS.get(market, "")


def get_user_snippet(market: str) -> str:
    """Return the market-specific user prompt snippet, empty string if unknown."""
    return MARKET_USER_SNIPPETS.get(market, "")
