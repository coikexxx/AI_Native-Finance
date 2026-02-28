"""Anthropic Claude API client with retry logic and per-job token tracking."""
import anthropic
import asyncio
import json
import re
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Type, TypeVar
from pydantic import BaseModel
from app.config import settings
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# ─── Per-job context vars (set by orchestrator before each analysis) ──────────
# ContextVar is per-asyncio-Task, so concurrent jobs don't interfere.
_ctx_job_id: ContextVar[str | None] = ContextVar('ctx_job_id', default=None)
_ctx_model: ContextVar[str | None] = ContextVar('ctx_model', default=None)
_ctx_api_key: ContextVar[str | None] = ContextVar('ctx_api_key', default=None)
_ctx_max_tokens: ContextVar[int | None] = ContextVar('ctx_max_tokens', default=None)


def set_job_context(job_id: str, model: str, api_key: str, max_tokens: int) -> None:
    """Called by the orchestrator at the start of each analysis job."""
    _ctx_job_id.set(job_id)
    _ctx_model.set(model)
    _ctx_api_key.set(api_key)
    _ctx_max_tokens.set(max_tokens)


# ─── Token accumulator ────────────────────────────────────────────────────────
@dataclass
class UsageAccumulator:
    input_tokens: int = 0
    output_tokens: int = 0


# ─── Client ───────────────────────────────────────────────────────────────────
class AnthropicClient:
    def __init__(self):
        self._usage: dict[str, UsageAccumulator] = {}

    # Token accumulator API
    def register_job(self, job_id: str) -> None:
        """Register a job for token tracking before running agents."""
        self._usage[job_id] = UsageAccumulator()

    def get_usage(self, job_id: str) -> UsageAccumulator:
        """Return accumulated token counts for a job."""
        return self._usage.get(job_id, UsageAccumulator())

    def clear_job(self, job_id: str) -> None:
        """Release memory after usage has been persisted."""
        self._usage.pop(job_id, None)

    def _make_client(self) -> anthropic.AsyncAnthropic:
        """Create a fresh Anthropic client using current job context (or env fallback)."""
        api_key = _ctx_api_key.get() or settings.anthropic_api_key
        return anthropic.AsyncAnthropic(api_key=api_key)

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = None,
        max_retries: int = 3,
    ) -> str:
        """Send a completion request and return the text response."""
        effective_model = _ctx_model.get() or settings.llm_model
        effective_max_tokens = max_tokens or _ctx_max_tokens.get() or settings.llm_max_tokens
        job_id = _ctx_job_id.get()

        for attempt in range(max_retries):
            try:
                client = self._make_client()
                message = await client.messages.create(
                    model=effective_model,
                    max_tokens=effective_max_tokens,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )

                # Accumulate token usage for the current job
                if job_id and job_id in self._usage:
                    self._usage[job_id].input_tokens += message.usage.input_tokens
                    self._usage[job_id].output_tokens += message.usage.output_tokens

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
    match = re.search(r"<json>(.*?)</json>", text, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
    else:
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
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
