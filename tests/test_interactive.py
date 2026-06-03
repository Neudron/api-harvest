"""Tests for InteractiveManager blocking-state tracking (offline)."""

from __future__ import annotations

import pytest
from rich.console import Console

from harvest.interactive import InteractiveManager


class _FakeDashboard:
    def __init__(self) -> None:
        self.paused = 0
        self.resumed = 0

    async def pause(self) -> None:
        self.paused += 1

    async def resume(self) -> None:
        self.resumed += 1


@pytest.mark.asyncio
async def test_blocking_flag_toggles_around_prompt() -> None:
    dash = _FakeDashboard()
    mgr = InteractiveManager(dashboard=dash, console=Console())  # type: ignore[arg-type]

    assert mgr.is_blocking_user is False

    # Simulate a prompt opening and closing via the internal pause/resume hooks.
    await mgr._pause()
    assert mgr.is_blocking_user is True
    await mgr._resume()
    assert mgr.is_blocking_user is False

    assert dash.paused == 1
    assert dash.resumed == 1


@pytest.mark.asyncio
async def test_nested_blocking_depth() -> None:
    mgr = InteractiveManager(dashboard=None, console=Console())

    await mgr._pause()
    await mgr._pause()
    assert mgr.is_blocking_user is True
    await mgr._resume()
    assert mgr.is_blocking_user is True  # still one open
    await mgr._resume()
    assert mgr.is_blocking_user is False


@pytest.mark.asyncio
async def test_resume_never_goes_negative() -> None:
    mgr = InteractiveManager(dashboard=None, console=Console())
    # Extra resume without a matching pause must not underflow.
    await mgr._resume()
    assert mgr.is_blocking_user is False
    await mgr._pause()
    assert mgr.is_blocking_user is True
