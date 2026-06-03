"""Tests for the multi-sink EventBus and JsonlEventSink (offline)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from harvest.events import EventBus, JsonlEventSink
from harvest.models import EventKind, StepEvent


def _ev(slug: str, kind: EventKind = EventKind.LOG, msg: str = "") -> StepEvent:
    return StepEvent(provider_slug=slug, kind=kind, message=msg)


@pytest.mark.asyncio
async def test_single_subscriber_receives_events() -> None:
    bus = EventBus()
    stream = bus.subscribe()
    await bus.emit(_ev("groq", msg="hello"))
    await bus.close()

    received = [e async for e in stream]
    assert len(received) == 1
    assert received[0].provider_slug == "groq"
    assert received[0].message == "hello"


@pytest.mark.asyncio
async def test_two_subscribers_both_receive_every_event() -> None:
    """The key fan-out guarantee: every subscriber sees every event."""
    bus = EventBus()
    s1 = bus.subscribe()
    s2 = bus.subscribe()

    await bus.emit(_ev("a"))
    await bus.emit(_ev("b"))
    await bus.emit(_ev("c"))
    await bus.close()

    got1 = [e.provider_slug async for e in s1]
    got2 = [e.provider_slug async for e in s2]
    assert got1 == ["a", "b", "c"]
    assert got2 == ["a", "b", "c"]


@pytest.mark.asyncio
async def test_stream_is_backcompat_alias() -> None:
    bus = EventBus()
    stream = bus.stream()  # legacy API
    await bus.emit(_ev("x"))
    await bus.close()
    got = [e.provider_slug async for e in stream]
    assert got == ["x"]


@pytest.mark.asyncio
async def test_close_terminates_all_subscribers() -> None:
    bus = EventBus()
    s1 = bus.subscribe()
    s2 = bus.subscribe()
    await bus.close()
    # Both streams should terminate cleanly (no hang, no events).
    assert [e async for e in s1] == []
    assert [e async for e in s2] == []


@pytest.mark.asyncio
async def test_late_subscriber_misses_earlier_events() -> None:
    """Documents the fan-out contract: subscribe before emitting."""
    bus = EventBus()
    await bus.emit(_ev("early"))  # no subscribers yet → dropped
    late = bus.subscribe()
    await bus.emit(_ev("late"))
    await bus.close()
    got = [e.provider_slug async for e in late]
    assert got == ["late"]


def test_jsonl_sink_serialize() -> None:
    line = JsonlEventSink.serialize(_ev("groq", kind=EventKind.SUCCESS, msg="done"))
    data = json.loads(line)
    assert data["provider_slug"] == "groq"
    assert data["kind"] == "success"
    assert data["message"] == "done"


@pytest.mark.asyncio
async def test_jsonl_sink_writes_events(tmp_path: Path) -> None:
    bus = EventBus()
    sink = JsonlEventSink(tmp_path / "events.jsonl")
    stream = bus.subscribe()

    import asyncio

    task = asyncio.create_task(sink.run(bus, events=stream))
    await bus.emit(_ev("a", kind=EventKind.START))
    await bus.emit(_ev("a", kind=EventKind.SUCCESS, msg="key"))
    await bus.close()
    await asyncio.wait_for(task, timeout=2.0)

    lines = (tmp_path / "events.jsonl").read_text().strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["kind"] == "start"
    assert json.loads(lines[1])["kind"] == "success"
    assert json.loads(lines[1])["message"] == "key"
