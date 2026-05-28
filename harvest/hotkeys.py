"""Reads single keys from stdin without echo and emits events.

The dashboard advertises [s] skip, [q] quit, [p] pause. This module listens
for those keys in a background asyncio task and pushes corresponding events
on the EventBus. Orchestrator + handlers consume those events at safe
checkpoints. If stdin is not a TTY (e.g. tests, CI), the task exits cleanly
without doing anything.
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass

from harvest.events import EventBus
from harvest.models import EventKind, StepEvent


@dataclass
class HotkeyState:
    skip_requested: bool = False
    quit_requested: bool = False
    paused: asyncio.Event = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.paused is None:
            self.paused = asyncio.Event()
            self.paused.set()  # set = NOT paused


async def run_hotkey_listener(state: HotkeyState, bus: EventBus) -> None:
    """Background task. Reads one byte at a time from stdin in raw mode."""
    if not sys.stdin.isatty():
        return  # nothing useful to listen to

    try:
        import termios
        import tty
    except ImportError:
        return  # Windows or unsupported

    fd = sys.stdin.fileno()
    try:
        old = termios.tcgetattr(fd)
    except termios.error:
        return

    loop = asyncio.get_running_loop()

    def _read_one() -> str | None:
        try:
            return sys.stdin.read(1)
        except Exception:
            return None

    try:
        tty.setcbreak(fd)
        while not state.quit_requested:
            ch = await loop.run_in_executor(None, _read_one)
            if not ch:
                continue
            ch = ch.lower()
            if ch == "s":
                state.skip_requested = True
                await bus.emit(
                    StepEvent(provider_slug="", kind=EventKind.SKIP_REQUESTED, message="hotkey s")
                )
            elif ch == "q":
                state.quit_requested = True
                await bus.emit(
                    StepEvent(provider_slug="", kind=EventKind.QUIT_REQUESTED, message="hotkey q")
                )
                break
            elif ch == "p":
                if state.paused.is_set():
                    state.paused.clear()
                    await bus.emit(
                        StepEvent(provider_slug="", kind=EventKind.DASHBOARD_PAUSE, message="hotkey p")
                    )
                else:
                    state.paused.set()
                    await bus.emit(
                        StepEvent(provider_slug="", kind=EventKind.DASHBOARD_RESUME, message="hotkey p")
                    )
    except asyncio.CancelledError:
        pass
    finally:
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        except Exception:
            pass
