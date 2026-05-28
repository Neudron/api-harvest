from __future__ import annotations

import asyncio
from collections import deque

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table
from rich.text import Text

from harvest.events import EventBus
from harvest.models import EventKind, ProviderSpec, StepEvent

_STATUS_STYLES = {
    "done": "bold green",
    "running": "bold yellow",
    "failed": "bold red",
    "skipped": "dim",
    "pending": "white",
}


class Dashboard:
    def __init__(self, console: Console, specs: list[ProviderSpec]):
        self.console = console
        self.specs = specs
        self.total = len(specs)
        self.statuses: dict[str, str] = {s.slug: "pending" for s in specs}
        self.keys_preview: dict[str, str] = {}
        self.notes: dict[str, str] = {}
        self.current_slug: str | None = None
        self.current_step: str = "—"
        self.recent: deque[str] = deque(maxlen=10)
        self.paused = asyncio.Event()
        self.paused.set()  # set = NOT paused
        self._live: Live | None = None
        self._layout = self._build_layout()
        self._progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            console=console,
            transient=False,
        )
        self._task_id = self._progress.add_task("Harvesting", total=self.total)

    def _build_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3),
        )
        layout["body"].split_row(
            Layout(name="providers", ratio=2),
            Layout(name="side", ratio=1),
        )
        layout["side"].split_column(
            Layout(name="current", size=5),
            Layout(name="progress", size=4),
            Layout(name="recent"),
        )
        return layout

    def _counts(self) -> dict[str, int]:
        counts = {"done": 0, "failed": 0, "skipped": 0, "running": 0, "pending": 0}
        for v in self.statuses.values():
            counts[v] = counts.get(v, 0) + 1
        return counts

    def _render_header(self) -> Panel:
        c = self._counts()
        text = Text()
        text.append("api-harvest  ", style="bold cyan")
        text.append(f"done {c['done']}/{self.total}  ", style="green")
        text.append(f"failed {c['failed']}  ", style="red")
        text.append(f"skipped {c['skipped']}  ", style="yellow")
        text.append(f"pending {c['pending']}", style="white")
        return Panel(text, border_style="cyan")

    def _render_providers(self) -> Panel:
        table = Table(show_header=True, header_style="bold magenta", expand=True)
        table.add_column("Tier", width=4)
        table.add_column("Provider", overflow="fold")
        table.add_column("Status", width=8)
        table.add_column("Key/Note", overflow="fold")
        for spec in self.specs:
            status = self.statuses.get(spec.slug, "pending")
            style = _STATUS_STYLES.get(status, "white")
            preview = self.keys_preview.get(spec.slug) or self.notes.get(spec.slug, "")
            table.add_row(
                f"T{spec.tier}",
                spec.name,
                Text(status.upper(), style=style),
                preview,
            )
        return Panel(table, title="Providers", border_style="blue")

    def _render_current(self) -> Panel:
        slug = self.current_slug or "—"
        name = next((s.name for s in self.specs if s.slug == slug), slug)
        text = Text()
        text.append(f"Now: {name}\n", style="bold yellow")
        text.append(f"Step: {self.current_step}", style="cyan")
        return Panel(text, border_style="yellow")

    def _render_recent(self) -> Panel:
        text = Text()
        for line in self.recent:
            text.append(line + "\n")
        return Panel(text, title="Recent", border_style="dim")

    def _render_footer(self) -> Panel:
        return Panel(
            Text("Hotkeys: [s] skip current   [q] quit gracefully   [p] pause", style="dim"),
            border_style="cyan",
        )

    def _refresh(self) -> None:
        self._layout["header"].update(self._render_header())
        self._layout["providers"].update(self._render_providers())
        self._layout["current"].update(self._render_current())
        self._layout["progress"].update(Panel(self._progress, border_style="green"))
        self._layout["recent"].update(self._render_recent())
        self._layout["footer"].update(self._render_footer())

    async def run(self, bus: EventBus) -> None:
        self._refresh()
        self._live = Live(self._layout, console=self.console, refresh_per_second=8, screen=False)
        self._live.start()
        try:
            async for event in bus.stream():
                self._apply(event)
                if self._live is not None and self.paused.is_set():
                    self._refresh()
                    self._live.refresh()
        finally:
            if self._live is not None:
                self._live.stop()

    def _apply(self, event: StepEvent) -> None:
        slug = event.provider_slug
        if event.kind == EventKind.START:
            self.current_slug = slug
            self.current_step = "starting"
            self.statuses[slug] = "running"
            self.recent.append(f"[{slug}] start")
        elif event.kind == EventKind.STEP:
            self.current_step = event.message
            self.recent.append(f"[{slug}] {event.message}")
        elif event.kind == EventKind.LOG:
            self.recent.append(f"[{slug}] {event.message}")
        elif event.kind == EventKind.SUCCESS:
            self.statuses[slug] = "done"
            key = event.payload.get("api_key") or ""
            if key:
                self.keys_preview[slug] = f"{key[:4]}…{key[-4:]}"
            done = sum(1 for v in self.statuses.values() if v == "done")
            self._progress.update(self._task_id, completed=done)
            self.recent.append(f"[{slug}] ✓ key captured")
        elif event.kind == EventKind.SKIP:
            self.statuses[slug] = "skipped"
            self.notes[slug] = event.message[:40]
            self.recent.append(f"[{slug}] skipped: {event.message}")
        elif event.kind == EventKind.FAIL:
            self.statuses[slug] = "failed"
            self.notes[slug] = event.message[:40]
            self.recent.append(f"[{slug}] ✗ {event.message}")
        elif event.kind == EventKind.AI_CALL:
            self.recent.append(f"[ai] {event.message}")
        elif event.kind == EventKind.PROMPT:
            self.recent.append(f"[prompt] {event.message}")
        elif event.kind == EventKind.DASHBOARD_PAUSE:
            self.paused.clear()
            if self._live is not None:
                self._live.stop()
        elif event.kind == EventKind.DASHBOARD_RESUME:
            self.paused.set()
            if self._live is not None:
                self._live.start()

    async def pause(self) -> None:
        self.paused.clear()
        if self._live is not None:
            self._live.stop()

    async def resume(self) -> None:
        self.paused.set()
        if self._live is not None:
            self._live.start()
