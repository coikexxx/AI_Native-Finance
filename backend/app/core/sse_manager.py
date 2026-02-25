"""Server-Sent Events connection manager."""
import asyncio
import json
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class SSEConnectionManager:
    """
    Manages SSE connections for:
    1. Analysis progress streams (job-specific)
    2. Global notification streams (alert triggers)
    """

    def __init__(self):
        # job_id → list of asyncio.Queue
        self._analysis_queues: Dict[str, List[asyncio.Queue]] = {}
        # Global notification queues (one per connected client)
        self._notification_queues: List[asyncio.Queue] = []

    def create_analysis_stream(self, job_id: str) -> asyncio.Queue:
        """Register a new SSE client for a specific job."""
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        if job_id not in self._analysis_queues:
            self._analysis_queues[job_id] = []
        self._analysis_queues[job_id].append(q)
        return q

    def remove_analysis_stream(self, job_id: str, queue: asyncio.Queue) -> None:
        if job_id in self._analysis_queues:
            try:
                self._analysis_queues[job_id].remove(queue)
            except ValueError:
                pass
            if not self._analysis_queues[job_id]:
                del self._analysis_queues[job_id]

    def create_notification_stream(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._notification_queues.append(q)
        return q

    def remove_notification_stream(self, queue: asyncio.Queue) -> None:
        try:
            self._notification_queues.remove(queue)
        except ValueError:
            pass

    async def push_analysis_event(self, job_id: str, event: dict) -> None:
        """Push event to all SSE clients watching this job."""
        queues = self._analysis_queues.get(job_id, [])
        for q in list(queues):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning(f"SSE queue full for job {job_id}, dropping event")

    async def push_notification(self, event: dict) -> None:
        """Push notification to all connected frontend clients."""
        for q in list(self._notification_queues):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass

    def format_sse(self, data: dict) -> str:
        """Format dict as SSE data line."""
        return f"data: {json.dumps(data)}\n\n"


sse_manager = SSEConnectionManager()
