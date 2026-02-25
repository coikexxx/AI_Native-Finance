"""Anthropic Claude API client with retry logic."""
import anthropic
import asyncio
import json
import re
from typing import Type, TypeVar
from pydantic import BaseModel
from app.config import settings
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class AnthropicClient:
    def __init__(self):
        self._client: anthropic.AsyncAnthropic | None = None

    def _get_client(self) -> anthropic.AsyncAnthropic:
        if self._client is None:
            self._client = anthropic.AsyncAnthropic(
                api_key=settings.anthropic_api_key,
            )
        return self._client

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = None,
        max_retries: int = 3,
    ) -> str:
        """Send a completion request and return the text response."""
        client = self._get_client()
        max_tokens = max_tokens or settings.llm_max_tokens

        for attempt in range(max_retries):
            try:
                message = await client.messages.create(
                    model=settings.llm_model,
                    max_tokens=max_tokens,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                return message.content[0].text
            except anthropic.RateLimitError:
                wait = 2 ** attempt
                logger.warning(f"Rate limit hit, waiting {wait}s (attempt {attempt + 1})")
                await asyncio.sleep(wait)
            except anthropic.APIError as e:
                if attempt == max_retries - 1:
                    raise
                logger.error(f"API error on attempt {attempt + 1}: {e}")
                await asyncio.sleep(2 ** attempt)
        raise RuntimeError("Max retries exceeded for LLM call")

    async def complete_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: Type[T],
        max_tokens: int = None,
    ) -> T:
        """Send a completion request and parse the JSON response into a Pydantic model."""
        schema_json = json.dumps(output_schema.model_json_schema(), indent=2)
        full_system = f"""{system_prompt}

You MUST respond with a valid JSON object that conforms to this schema:
<schema>
{schema_json}
</schema>

Wrap your JSON response in <json> tags:
<json>
{{...your response...}}
</json>"""

        response_text = await self.complete(full_system, user_prompt, max_tokens)
        return parse_structured_output(response_text, output_schema)


def parse_structured_output(text: str, schema: Type[T]) -> T:
    """Extract JSON from <json> tags and parse into Pydantic model."""
    # Try <json> tags first
    match = re.search(r"<json>(.*?)</json>", text, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
    else:
        # Try to find raw JSON block
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            # Last resort: find first { to last }
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1:
                raise ValueError(f"No JSON found in LLM response: {text[:200]}")
            json_str = text[start:end + 1]

    try:
        data = json.loads(json_str)
        return schema.model_validate(data)
    except Exception as e:
        logger.error(f"JSON parse error for schema {schema.__name__}: {e}\nText: {text[:500]}")
        raise ValueError(f"Failed to parse LLM output as {schema.__name__}: {e}")


llm_client = AnthropicClient()
