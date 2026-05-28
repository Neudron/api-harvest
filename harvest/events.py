from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from harvest.models import EventKind, StepEvent


class EventBus:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[StepEvent | None] = asyncio.Queue()

    async def emit(self, event: StepEvent) -> None:
        await self._queue.put(event)

    async def close(self) -> None:
        await self._queue.put(None)

    async def stream(self) -> AsyncIterator[StepEvent]:
        while True:
            event = await self._queue.get()
            if event is None:
                return
            yield event


async def emit_log(bus: EventBus, slug: str, message: str) -> None:
    await bus.emit(StepEvent(provider_slug=slug, kind=EventKind.LOG, message=message))


async def emit_step(bus: EventBus, slug: str, message: str) -> None:
    await bus.emit(StepEvent(provider_slug=slug, kind=EventKind.STEP, message=message))
