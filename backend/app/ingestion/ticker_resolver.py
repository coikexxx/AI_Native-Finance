"""
Market-aware ticker resolver.

Accepts user input in short form (e.g. "600519", "0700", "BTC") and returns
a fully-qualified yfinance ticker along with market metadata.

Supported markets:
  a_share  – A-shares on SSE (suffix .SS) or SZSE (suffix .SZ)
  hk       – Hong Kong stocks on HKEX (suffix .HK)
  crypto   – Bitcoin / BTC (ticker BTC-USD)
"""
import re
from typing import TypedDict


class TickerInfo(TypedDict):
    yf_ticker: str        # ticker passed to yfinance, e.g. "600519.SS"
    display: str          # short display code shown in UI, e.g. "600519"
    market: str           # "a_share" | "hk" | "crypto" | "unknown"
    currency: str         # "¥" | "HK$" | "$"
    currency_code: str    # "CNY" | "HKD" | "USD"
    exchange: str         # "SSE" | "SZSE" | "HKEX" | "Crypto" | "Unknown"
    trading_hours: str    # human-readable trading session (Chinese)
    market_name_cn: str   # market label in Chinese


# ── BTC aliases ───────────────────────────────────────────────────────────────
_BTC_ALIASES = {"BTC", "BITCOIN", "BTC-USD", "BTC/USD", "BTCUSD"}

# ── Regex helpers ─────────────────────────────────────────────────────────────
_RE_6DIGIT = re.compile(r"^\d{6}$")   # 6-digit A-share code
_RE_HK     = re.compile(r"^\d{2,5}$") # 2–5 digit HK stock code


def resolve_ticker(user_input: str) -> TickerInfo:
    """
    Resolve a user-supplied ticker string to a yfinance-compatible format.

    Raises ValueError if the input cannot be mapped to a supported market.
    """
    t = user_input.strip().upper()

    # ── Bitcoin ───────────────────────────────────────────────────────────────
    if t in _BTC_ALIASES:
        return TickerInfo(
            yf_ticker="BTC-USD",
            display="BTC",
            market="crypto",
            currency="$",
            currency_code="USD",
            exchange="Crypto",
            trading_hours="24/7（全天候交易）",
            market_name_cn="加密货币",
        )

    # ── Already has exchange suffix ───────────────────────────────────────────
    if t.endswith(".SS"):
        return TickerInfo(
            yf_ticker=t,
            display=t.replace(".SS", ""),
            market="a_share",
            currency="¥",
            currency_code="CNY",
            exchange="SSE",
            trading_hours="09:30–15:00 CST 周一至周五",
            market_name_cn="A股（沪市）",
        )
    if t.endswith(".SZ"):
        return TickerInfo(
            yf_ticker=t,
            display=t.replace(".SZ", ""),
            market="a_share",
            currency="¥",
            currency_code="CNY",
            exchange="SZSE",
            trading_hours="09:30–15:00 CST 周一至周五",
            market_name_cn="A股（深市）",
        )
    if t.endswith(".HK"):
        code = t.replace(".HK", "")
        padded = code.zfill(4)
        return TickerInfo(
            yf_ticker=f"{padded}.HK",
            display=code,
            market="hk",
            currency="HK$",
            currency_code="HKD",
            exchange="HKEX",
            trading_hours="09:30–16:00 HKT 周一至周五",
            market_name_cn="港股",
        )

    # ── Pure-digit input ──────────────────────────────────────────────────────
    if t.isdigit():
        if _RE_6DIGIT.match(t):
            # A-share: Shanghai codes start with 6; Shenzhen starts with 0/2/3
            if t.startswith("6"):
                return TickerInfo(
                    yf_ticker=f"{t}.SS",
                    display=t,
                    market="a_share",
                    currency="¥",
                    currency_code="CNY",
                    exchange="SSE",
                    trading_hours="09:30–15:00 CST 周一至周五",
                    market_name_cn="A股（沪市）",
                )
            else:
                return TickerInfo(
                    yf_ticker=f"{t}.SZ",
                    display=t,
                    market="a_share",
                    currency="¥",
                    currency_code="CNY",
                    exchange="SZSE",
                    trading_hours="09:30–15:00 CST 周一至周五",
                    market_name_cn="A股（深市）",
                )
        if _RE_HK.match(t):
            # HK stock: zero-pad to 4 digits
            padded = t.zfill(4)
            return TickerInfo(
                yf_ticker=f"{padded}.HK",
                display=t,
                market="hk",
                currency="HK$",
                currency_code="HKD",
                exchange="HKEX",
                trading_hours="09:30–16:00 HKT 周一至周五",
                market_name_cn="港股",
            )

    # ── Unsupported (e.g. plain US letters like AAPL) ─────────────────────────
    raise ValueError(
        f"不支持的股票代码: '{user_input}'。"
        "本平台仅支持 A股（如 600519）、港股（如 0700）和 BTC。"
    )
