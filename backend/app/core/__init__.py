"""Core exports with lazy loading to avoid import-time side effects."""

from app.core.sse_manager import sse_manager, SSEConnectionManager

__all__ = ["orchestrator", "AgentOrchestrator", "sse_manager", "SSEConnectionManager"]


def __getattr__(name: str):
    if name in {"orchestrator", "AgentOrchestrator"}:
        from app.core.orchestrator import orchestrator, AgentOrchestrator

        return {"orchestrator": orchestrator, "AgentOrchestrator": AgentOrchestrator}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
