"""Server-Sent Events connection manager."""
import asyncio
import json
from typing import Dict, List
import logging
import os

logger = logging.getLogger(__name__)


class SSEConnectionManager:
    """
    Manages SSE connections for:
    1. Analysis progress streams (job-specific)
    2. Global notification streams (alert triggers)
    """

    TERMINAL_EVENT_TYPES = {"complete", "error"}

    def __init__(self, analysis_queue_size: int | None = None):
        self._analysis_queue_size = analysis_queue_size or int(os.getenv("SSE_QUEUE_SIZE", "200"))

        # job_id → list of asyncio.Queue
        self._analysis_queues: Dict[str, List[asyncio.Queue]] = {}
        # Global notification queues (one per connected client)
        self._notification_queues: List[asyncio.Queue] = []
        # job_id -> dropped non-terminal event count
        self._dropped_analysis_events: Dict[str, int] = {}

    def create_analysis_stream(self, job_id: str) -> asyncio.Queue:
        """Register a new SSE client for a specific job."""
        q: asyncio.Queue = asyncio.Queue(maxsize=self._analysis_queue_size)
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

    def _record_drop(self, job_id: str) -> None:
        dropped = self._dropped_analysis_events.get(job_id, 0) + 1
        self._dropped_analysis_events[job_id] = dropped
        if dropped % 25 == 0:
            logger.warning("Dropped %s SSE non-terminal events for job %s", dropped, job_id)

    def _queue_put_with_priority(self, q: asyncio.Queue, event: dict, is_terminal: bool, job_id: str) -> None:
        try:
            q.put_nowait(event)
            return
        except asyncio.QueueFull:
            if not is_terminal:
                self._record_drop(job_id)
                return

        # Terminal event: make room by evicting oldest items until there is space.
        while True:
            try:
                _ = q.get_nowait()
            except asyncio.QueueEmpty:
                break
            try:
                q.put_nowait(event)
                return
            except asyncio.QueueFull:
                continue

        # Should be rare, but keep observable.
        logger.error("Unable to enqueue terminal SSE event for job %s", job_id)

    async def push_analysis_event(self, job_id: str, event: dict) -> None:
        """Push event to all SSE clients watching this job."""
        queues = self._analysis_queues.get(job_id, [])
        event_type = event.get("event_type", "")
        is_terminal = event_type in self.TERMINAL_EVENT_TYPES

        for q in list(queues):
            self._queue_put_with_priority(q, event, is_terminal=is_terminal, job_id=job_id)

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
