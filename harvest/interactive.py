from __future__ import annotations

import asyncio
import sys
from typing import Literal

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from rich.console import Console

from harvest.dashboard import Dashboard

_session: PromptSession | None = None


def _get_session() -> PromptSession:
    global _session
    if _session is None:
        _session = PromptSession()
    return _session


async def _async_prompt(prompt_text: str) -> str:
    """Non-blocking stdin prompt that plays nicely with rich.live.Live."""
    session = _get_session()
    with patch_stdout():
        return await session.prompt_async(prompt_text)


class InteractiveManager:
    """Coordinates pause/resume between dashboard Live and stdin prompts."""

    def __init__(self, dashboard: Dashboard | None, console: Console):
        self.dashboard = dashboard
        self.console = console

    async def _pause(self) -> None:
        if self.dashboard is not None:
            await self.dashboard.pause()

    async def _resume(self) -> None:
        if self.dashboard is not None:
            await self.dashboard.resume()

    async def ask_sms_code(self, provider_name: str, phone_hint: str | None = None) -> str:
        await self._pause()
        try:
            self.console.rule(f"[yellow]SMS verification: {provider_name}[/yellow]")
            if phone_hint:
                self.console.print(f"  phone hint: {phone_hint}")
            self.console.print("  Enter the SMS code you received, then press Enter.")
            code = await _async_prompt("SMS code> ")
            return code.strip()
        finally:
            await self._resume()

    async def pause_for_cc(self, provider_name: str, why: str) -> Literal["resume", "skip"]:
        await self._pause()
        try:
            self.console.rule(f"[red]Credit card required: {provider_name}[/red]")
            self.console.print(f"  {why}")
            self.console.print("  [r]esume after entering CC in the browser, or [s]kip this provider.")
            while True:
                resp = (await _async_prompt("r/s> ")).strip().lower()
                if resp in ("r", "resume", ""):
                    return "resume"
                if resp in ("s", "skip"):
                    return "skip"
        finally:
            await self._resume()

    async def pause_for_manual_takeover(
        self, provider_name: str, message: str
    ) -> Literal["resume", "skip", "abort"]:
        await self._pause()
        try:
            self.console.rule(f"[magenta]Manual takeover: {provider_name}[/magenta]")
            self.console.print(f"  {message}")
            self.console.print("  [r]esume   [s]kip provider   [q]uit run")
            while True:
                resp = (await _async_prompt("r/s/q> ")).strip().lower()
                if resp in ("r", "resume", ""):
                    return "resume"
                if resp in ("s", "skip"):
                    return "skip"
                if resp in ("q", "quit", "abort"):
                    return "abort"
        finally:
            await self._resume()

    async def confirm(self, message: str) -> bool:
        await self._pause()
        try:
            resp = (await _async_prompt(f"{message} [y/N] ")).strip().lower()
            return resp in ("y", "yes")
        finally:
            await self._resume()

    async def prompt_value(self, label: str) -> str:
        """Read a free-form string from the user, pausing the dashboard around it."""
        await self._pause()
        try:
            return await _async_prompt(f"{label}> ")
        finally:
            await self._resume()


async def block_until_enter(prompt: str = "Press Enter to continue... ") -> None:
    """Used by tests / no-dashboard mode."""
    if sys.stdin.isatty():
        await _async_prompt(prompt)
    else:
        await asyncio.sleep(0)
