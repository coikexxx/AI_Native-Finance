"""Input validation and prompt guardrails."""
import re


VALID_TICKER_PATTERN = re.compile(r"^[A-Z]{1,5}(\.[A-Z]{1,2})?$")

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
    """Validate ticker format. Returns (is_valid, error_message)."""
    if not ticker:
        return False, "Ticker cannot be empty"
    ticker = ticker.strip().upper()
    if not VALID_TICKER_PATTERN.match(ticker):
        return False, f"Invalid ticker format: '{ticker}'. Expected 1-5 uppercase letters, optionally followed by .XX"
    if len(ticker) > 10:
        return False, "Ticker too long"
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
