from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import asdict
from pathlib import Path

from harvest.models import EventKind, StepEvent


class EventBus:
    """Async event bus with multi-subscriber fan-out.

    Back-compat: ``stream()`` still works as a single subscription (the
    dashboard uses it), and ``emit()``/``close()`` keep their signatures. New
    consumers (structured logging, JSONL audit, reporting) call ``subscribe()``
    to get their own independent stream — every subscriber receives every event.

    Each subscriber has its own unbounded queue, so a slow consumer can't drop
    another's events; ``emit()`` never blocks on a subscriber.
    """

    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue[StepEvent | None]] = []
        self._closed = False

    def subscribe(self) -> AsyncIterator[StepEvent]:
        """Register a new subscriber and return its event iterator."""
        queue: asyncio.Queue[StepEvent | None] = asyncio.Queue()
        self._subscribers.append(queue)
        return self._iter(queue)

    async def _iter(self, queue: asyncio.Queue[StepEvent | None]) -> AsyncIterator[StepEvent]:
        while True:
            event = await queue.get()
            if event is None:
                return
            yield event

    async def emit(self, event: StepEvent) -> None:
        for queue in self._subscribers:
            await queue.put(event)

    async def close(self) -> None:
        self._closed = True
        for queue in self._subscribers:
            await queue.put(None)

    def stream(self) -> AsyncIterator[StepEvent]:
        """Back-compat single subscription (equivalent to ``subscribe()``)."""
        return self.subscribe()


class JsonlEventSink:
    """Subscribes to an EventBus and appends every event to a JSONL file.

    Pure I/O sink — drive it with ``await sink.run(bus)`` as a background task,
    alongside the dashboard. Useful for post-run reporting and debugging.
    """

    def __init__(self, path: Path):
        self.path = path

    @staticmethod
    def serialize(event: StepEvent) -> str:
        """Render a StepEvent as a single JSON line (kind as its string value)."""
        data = asdict(event)
        data["kind"] = str(event.kind)
        return json.dumps(data)

    async def run(self, bus: EventBus, events: AsyncIterator[StepEvent] | None = None) -> None:
        stream = events if events is not None else bus.subscribe()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            async for event in stream:
                f.write(self.serialize(event) + "\n")
                f.flush()


async def emit_log(bus: EventBus, slug: str, message: str) -> None:
    await bus.emit(StepEvent(provider_slug=slug, kind=EventKind.LOG, message=message))


async def emit_step(bus: EventBus, slug: str, message: str) -> None:
    await bus.emit(StepEvent(provider_slug=slug, kind=EventKind.STEP, message=message))
