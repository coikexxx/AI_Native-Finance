"""Input validation and prompt guardrails."""
import re


# Accepts:
#   - 6-digit A-share codes with .SS/.SZ  (e.g. 600519.SS, 000858.SZ)
#   - 2–5 digit HK codes with .HK         (e.g. 0700.HK, 9988.HK)
#   - BTC-USD                              (Bitcoin)
#   - Short-form inputs resolved upstream  (e.g. 600519, 0700, BTC)
#   - Legacy 1–5 letter codes kept for internal use (e.g. BTC)
VALID_TICKER_PATTERN = re.compile(
    r"^([A-Z]{1,7}|[0-9]{2,6})([\.\-][A-Z]{1,3})?$"
)

# Patterns that indicate prompt injection attempts
INJECTION_PATTERNS = [
    r"ignore previous",
    r"ignore all instructions",
    r"disregard",
    r"new instructions",
    r"act as",
    r"jailbreak",
    r"system prompt",
    r"<\|.*?\|>",
]


def validate_ticker(ticker: str) -> tuple[bool, str | None]:
    """
    Validate ticker format, then confirm it maps to a supported market.
    Returns (is_valid, error_message).
    """
    if not ticker:
        return False, "股票代码不能为空 / Ticker cannot be empty"
    ticker = ticker.strip().upper()
    if len(ticker) > 12:
        return False, "股票代码过长 / Ticker too long"
    if not VALID_TICKER_PATTERN.match(ticker):
        return False, (
            f"不支持的代码格式: '{ticker}'。"
            "请输入A股代码（如 600519）、港股代码（如 0700）或 BTC。"
        )
    # Market-level check via resolver
    try:
        from app.ingestion.ticker_resolver import resolve_ticker
        resolve_ticker(ticker)  # raises ValueError for unsupported markets
    except ValueError as e:
        return False, str(e)
    return True, None


def sanitize_input(text: str) -> tuple[str, bool]:
    """
    Sanitize user-provided text for inclusion in prompts.
    Returns (sanitized_text, was_modified).
    """
    if not text:
        return "", False

    original = text
    # Check for injection patterns
    lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lower):
            # Remove the suspicious content
            text = re.sub(pattern, "[REDACTED]", text, flags=re.IGNORECASE)

    # Limit length
    if len(text) > 2000:
        text = text[:2000] + "...[truncated]"

    return text, text != original
