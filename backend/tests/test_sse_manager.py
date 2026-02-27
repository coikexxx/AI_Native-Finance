import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.sse_manager import SSEConnectionManager


def test_terminal_event_survives_full_queue():
    async def scenario():
        manager = SSEConnectionManager(analysis_queue_size=5)
        q = manager.create_analysis_stream('job1')

        for i in range(q.maxsize):
            await manager.push_analysis_event('job1', {'event_type': 'agent_progress', 'payload': {'i': i}})

        await manager.push_analysis_event('job1', {'event_type': 'complete', 'payload': {'ok': True}})

        seen_complete = False
        while not q.empty():
            event = q.get_nowait()
            if event.get('event_type') == 'complete':
                seen_complete = True
                break

        assert seen_complete

    asyncio.run(scenario())


def test_non_terminal_drop_count_increases_when_full():
    async def scenario():
        manager = SSEConnectionManager(analysis_queue_size=3)
        q = manager.create_analysis_stream('job2')

        for i in range(q.maxsize):
            await manager.push_analysis_event('job2', {'event_type': 'agent_progress', 'payload': {'i': i}})

        await manager.push_analysis_event('job2', {'event_type': 'agent_progress', 'payload': {'i': 999}})
        assert manager._dropped_analysis_events.get('job2', 0) >= 1

    asyncio.run(scenario())
