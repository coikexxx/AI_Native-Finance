"""Citation management: assigns [E1]...[En] keys and builds evidence packs."""
from typing import List, Dict
from dataclasses import dataclass, field
import threading


@dataclass
class EvidenceEntry:
    key: str           # "[E1]"
    agent_name: str
    source_type: str
    source_label: str
    excerpt: str
    source_url: str = ""
    data_snapshot: dict = field(default_factory=dict)


class CitationMapper:
    """Thread-safe citation key assignment for one analysis job."""

    def __init__(self):
        self._entries: List[EvidenceEntry] = []
        self._lock = threading.Lock()
        self._counter = 0

    def add_evidence(
        self,
        agent_name: str,
        source_type: str,
        source_label: str,
        excerpt: str,
        source_url: str = "",
        data_snapshot: dict = None,
    ) -> str:
        """Register an evidence item and return its citation key."""
        with self._lock:
            self._counter += 1
            key = f"[E{self._counter}]"
            self._entries.append(EvidenceEntry(
                key=key,
                agent_name=agent_name,
                source_type=source_type,
                source_label=source_label,
                excerpt=excerpt[:1000],  # Cap excerpt length
                source_url=source_url or "",
                data_snapshot=data_snapshot or {},
            ))
            return key

    def get_all(self) -> List[EvidenceEntry]:
        with self._lock:
            return list(self._entries)

    def get_for_agent(self, agent_name: str) -> List[EvidenceEntry]:
        with self._lock:
            return [e for e in self._entries if e.agent_name == agent_name]

    def to_markdown(self) -> str:
        """Format evidence pack as markdown appendix."""
        lines = ["\n---\n## Evidence Pack\n"]
        for e in self._entries:
            lines.append(f"### {e.key} — {e.source_label}")
            lines.append(f"- **Agent**: {e.agent_name}")
            lines.append(f"- **Source type**: {e.source_type}")
            if e.source_url:
                lines.append(f"- **URL**: {e.source_url}")
            lines.append(f"\n> {e.excerpt}\n")
        return "\n".join(lines)
