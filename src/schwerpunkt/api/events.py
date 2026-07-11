from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, AsyncIterator


class EscalationBus:
    """In-process pub/sub for operator escalation SSE streams."""

    def __init__(self) -> None:
        self._queues: dict[str, list[asyncio.Queue[dict[str, Any]]]] = defaultdict(list)

    def publish(self, session_id: str, payload: dict[str, Any]) -> None:
        for queue in list(self._queues.get(session_id, [])):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                pass

    def subscribe(self, session_id: str) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=32)
        self._queues[session_id].append(queue)
        return queue

    def unsubscribe(self, session_id: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
        subs = self._queues.get(session_id, [])
        if queue in subs:
            subs.remove(queue)
        if not subs and session_id in self._queues:
            del self._queues[session_id]

    async def stream(self, session_id: str) -> AsyncIterator[dict[str, Any]]:
        queue = self.subscribe(session_id)
        try:
            while True:
                yield await queue.get()
        finally:
            self.unsubscribe(session_id, queue)


_bus: EscalationBus | None = None


def get_escalation_bus() -> EscalationBus:
    global _bus
    if _bus is None:
        _bus = EscalationBus()
    return _bus


def reset_escalation_bus() -> EscalationBus:
    global _bus
    _bus = EscalationBus()
    return _bus
