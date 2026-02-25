"""Abstract base class for all specialist agents."""
import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine, List, Optional, Type
from pydantic import BaseModel

from app.llm.client import llm_client
from app.storage.vector_store import VectorStore
from app.governance.citations import CitationMapper
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    agent_name: str = "BaseAgent"

    def __init__(
        self,
        job_id: str,
        ticker: str,
        citation_mapper: CitationMapper,
        vector_store: VectorStore,
        progress_callback: Optional[Callable[[str, int, str], Coroutine]] = None,
    ):
        self.job_id = job_id
        self.ticker = ticker
        self.citations = citation_mapper
        self.vector_store = vector_store
        self.progress_callback = progress_callback
        self._start_time = None

    @abstractmethod
    async def run(self, context: dict) -> dict:
        """
        Main agent logic. context contains all gathered data.
        Returns structured output dict.
        """
        ...

    async def emit_progress(self, pct: int, message: str) -> None:
        """Push SSE progress update for this agent."""
        if self.progress_callback:
            try:
                await self.progress_callback(self.agent_name, pct, message)
            except Exception:
                pass

    async def retrieve_context(
        self,
        query: str,
        collection_suffix: str = "general",
        n_results: int = 8,
    ) -> List[dict]:
        """RAG retrieval from ChromaDB for this ticker."""
        collection_name = f"{self.ticker.lower()}_{collection_suffix}"
        results = self.vector_store.query(
            collection_name=collection_name,
            query_text=query,
            n_results=n_results,
        )
        # Auto-log evidence for retrieved chunks
        for chunk in results[:3]:  # Log top-3 as evidence
            meta = chunk.get("metadata", {})
            self.citations.add_evidence(
                agent_name=self.agent_name,
                source_type=meta.get("source_type", "document"),
                source_label=meta.get("source_label", collection_suffix),
                excerpt=chunk.get("text", "")[:300],
                source_url=meta.get("source_url", ""),
            )
        return results

    async def call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: Type[BaseModel],
        max_tokens: int = 4096,
    ) -> BaseModel:
        """Call Claude with structured output parsing."""
        return await llm_client.complete_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            output_schema=output_schema,
            max_tokens=max_tokens,
        )

    async def call_llm_text(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
    ) -> str:
        """Call Claude for free-form text response."""
        return await llm_client.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
        )

    async def safe_run(self, context: dict) -> dict:
        """Wrapper that catches errors and returns fallback output."""
        self._start_time = time.time()
        try:
            await self.emit_progress(0, f"Starting {self.agent_name}...")
            result = await self.run(context)
            duration = int((time.time() - self._start_time) * 1000)
            logger.info(f"{self.agent_name} completed in {duration}ms for {self.ticker}")
            await self.emit_progress(100, f"{self.agent_name} complete")
            return result
        except Exception as e:
            logger.error(f"{self.agent_name} failed for {self.ticker}: {e}", exc_info=True)
            await self.emit_progress(100, f"{self.agent_name} encountered an error")
            return {"error": str(e), "agent": self.agent_name}
