from __future__ import annotations

import asyncio
import time
from collections import deque
from collections.abc import AsyncIterator

from rich.align import Align
from rich.console import Console, Group, RenderableType
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
)
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

from harvest.events import EventBus
from harvest.models import EventKind, ProviderSpec, StepEvent

# --- design system -----------------------------------------------------------
# Semantic palette (success/danger/warning/info) per common dashboard guidance.
ACCENT = "#5fd7ff"  # brand cyan, used for brand + structural borders
_OK = "green"
_RUN = "yellow"
_BAD = "red"
_MUTED = "grey50"
_INFO = "#5fafff"

# icon, text-style, short label — one entry per provider status.
_STATUS_META: dict[str, tuple[str, str, str]] = {
    "done": ("✓", f"bold {_OK}", "DONE"),
    "running": ("◐", f"bold {_RUN}", "RUN"),
    "failed": ("✗", f"bold {_BAD}", "FAIL"),
    "skipped": ("↷", _MUTED, "SKIP"),
    "pending": ("·", _MUTED, "WAIT"),
}

# Per-event-kind styling for the activity log.
_LOG_STYLE: dict[EventKind, tuple[str, str]] = {
    EventKind.START: ("▸", "cyan"),
    EventKind.STEP: ("·", "grey70"),
    EventKind.LOG: ("·", _MUTED),
    EventKind.SUCCESS: ("✓", f"bold {_OK}"),
    EventKind.SKIP: ("↷", _MUTED),
    EventKind.FAIL: ("✗", f"bold {_BAD}"),
    EventKind.RETRY: ("↻", _RUN),
    EventKind.AI_CALL: ("✦", "magenta"),
    EventKind.PROMPT: ("?", _INFO),
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
        # Structured recent log: (icon, style, text). Kept under the name
        # ``recent`` for continuity; rendered with per-kind colors.
        self.recent: deque[tuple[str, str, str]] = deque(maxlen=12)

        # Run-wide telemetry surfaced in the header / progress panels.
        self._start = time.monotonic()
        self.ai_calls = 0
        self.retries = 0
        self.prompt_active: str | None = None

        # ``paused`` (set == NOT paused) gates the Live refresh while an
        # interactive stdin prompt is open. ``_view_frozen`` is the *soft*
        # pause toggled by the [p] hotkey — it freezes refreshes without
        # tearing down Live, so the last frame stays on screen to read.
        self.paused = asyncio.Event()
        self.paused.set()
        self._view_frozen = False

        self._live: Live | None = None
        self._layout = self._build_layout()

        self._spinner = Spinner("dots", style=_RUN)
        # Slim progress: the side panel is narrow, and elapsed time already
        # lives in the header — so spend the width on the bar itself.
        self._progress = Progress(
            SpinnerColumn(style=ACCENT),
            BarColumn(bar_width=None, complete_style=_OK, finished_style=_OK),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            console=console,
            expand=True,
        )
        self._task_id = self._progress.add_task("harvesting", total=self.total)

    # -- layout ---------------------------------------------------------------
    def _build_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3),
        )
        layout["body"].split_row(
            Layout(name="providers", ratio=2),
            Layout(name="side", ratio=1, minimum_size=34),
        )
        layout["side"].split_column(
            Layout(name="current", size=6),
            Layout(name="progress", size=4),
            Layout(name="recent"),
        )
        return layout

    def _counts(self) -> dict[str, int]:
        counts = {"done": 0, "failed": 0, "skipped": 0, "running": 0, "pending": 0}
        for v in self.statuses.values():
            counts[v] = counts.get(v, 0) + 1
        return counts

    @staticmethod
    def _fmt_elapsed(seconds: float) -> str:
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    # -- header ---------------------------------------------------------------
    def _render_header(self) -> Panel:
        c = self._counts()
        pills = Text()
        for status in ("done", "running", "failed", "skipped", "pending"):
            icon, style, _ = _STATUS_META[status]
            n = c[status]
            chunk_style = style if n else _MUTED
            pills.append(f" {icon} ", style=chunk_style)
            pills.append(f"{n} ", style=f"bold {chunk_style}" if n else _MUTED)
            pills.append("  ")

        meta = Text(no_wrap=True)
        meta.append("⏱ ", style=_MUTED)
        meta.append(self._fmt_elapsed(time.monotonic() - self._start), style="bold white")
        meta.append("   ✦ ", style="magenta")
        meta.append(f"{self.ai_calls} AI", style="bold magenta")
        if self.retries:
            meta.append("   ↻ ", style=_RUN)
            meta.append(f"{self.retries}", style=f"bold {_RUN}")

        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="right")
        grid.add_row(pills, meta)
        return Panel(
            grid,
            title="[bold]⛏  api-harvest[/bold]",
            title_align="left",
            border_style=ACCENT,
            padding=(0, 1),
        )

    # -- providers table ------------------------------------------------------
    def _flags(self, spec: ProviderSpec) -> Text:
        t = Text()
        if spec.requires_cc:
            t.append("CC ", style=f"bold {_RUN}")
        if spec.requires_phone:
            t.append("SMS", style=f"bold {_INFO}")
        return t

    def _render_providers(self) -> Panel:
        table = Table(
            show_header=True,
            header_style=f"bold {ACCENT}",
            expand=True,
            box=None,
            pad_edge=False,
            padding=(0, 1),
        )
        table.add_column(" ", width=1, no_wrap=True)
        table.add_column("Status", width=7, no_wrap=True)
        table.add_column("Provider", ratio=4, overflow="ellipsis", no_wrap=True)
        table.add_column("", width=6, no_wrap=True)  # flags
        table.add_column("Key / Note", ratio=3, overflow="ellipsis", no_wrap=True)

        last_tier: int | None = None
        for spec in self.specs:
            if spec.tier != last_tier:
                label = "Permanent free" if spec.tier == 1 else "Trial credits"
                table.add_row(
                    "",
                    Text(f"TIER {spec.tier}", style="bold magenta"),
                    Text(label, style="italic magenta"),
                    "",
                    "",
                )
                last_tier = spec.tier

            status = self.statuses.get(spec.slug, "pending")
            icon, style, label = _STATUS_META.get(status, _STATUS_META["pending"])
            is_current = spec.slug == self.current_slug and status == "running"

            badge = Text(no_wrap=True)
            badge.append(f"{icon} ", style=style)
            badge.append(label, style=style)

            name = Text(spec.name, style="bold white" if is_current else "white")
            preview = self.keys_preview.get(spec.slug) or self.notes.get(spec.slug, "")
            preview_style = _OK if spec.slug in self.keys_preview else _MUTED
            marker = Text("▶", style=f"bold {_RUN}") if is_current else Text(" ")

            table.add_row(marker, badge, name, self._flags(spec), Text(preview, style=preview_style))

        done = self._counts()["done"]
        title = f"[bold]Providers[/bold]  [dim]{done}/{self.total} captured[/dim]"
        return Panel(table, title=title, title_align="left", border_style="blue", padding=(0, 1))

    # -- side: current --------------------------------------------------------
    def _render_current(self) -> Panel:
        slug = self.current_slug
        spec = next((s for s in self.specs if s.slug == slug), None)
        running = spec is not None and self.statuses.get(slug, "") == "running"

        grid = Table.grid(padding=(0, 1))
        grid.add_column(width=4, no_wrap=True)
        grid.add_column(overflow="fold")

        if spec is None:
            grid.add_row(Text("▸", style=_MUTED), Text("idle — waiting to start", style=_MUTED))
        else:
            tier = Text(f"T{spec.tier}", style="magenta")
            head = Text(spec.name, style=f"bold {_RUN}" if running else "bold white")
            head.append("  ")
            head.append_text(tier)
            grid.add_row(Text("▸", style=ACCENT), head)
            step_icon: RenderableType = self._spinner if running else Text("·", style=_MUTED)
            grid.add_row(step_icon, Text(self.current_step, style="cyan"))
            if self.prompt_active:
                grid.add_row(Text("?", style=_INFO), Text(self.prompt_active, style=f"bold {_INFO}"))

        border = _RUN if running else _MUTED
        return Panel(grid, title="[bold]Now[/bold]", title_align="left", border_style=border)

    # -- side: progress -------------------------------------------------------
    def _render_progress(self) -> Panel:
        return Panel(self._progress, title="[bold]Progress[/bold]", title_align="left", border_style=_OK)

    # -- side: recent log -----------------------------------------------------
    def _render_recent(self) -> Panel:
        if not self.recent:
            body: RenderableType = Align.center(Text("no activity yet", style=_MUTED), vertical="middle")
        else:
            lines = []
            for icon, style, text in self.recent:
                line = Text(no_wrap=True, overflow="ellipsis")
                line.append(f"{icon} ", style=style)
                line.append(text, style=style)
                lines.append(line)
            body = Group(*lines)
        return Panel(body, title="[bold]Activity[/bold]", title_align="left", border_style="grey37")

    # -- footer: keybindings --------------------------------------------------
    @staticmethod
    def _keycap(key: str, label: str, *, accent: str = "white") -> Text:
        t = Text()
        t.append(f" {key} ", style=f"bold black on {accent}")
        t.append(f" {label}", style="grey85")
        return t

    def _render_footer(self) -> Panel:
        row = Text()
        if self._view_frozen:
            row.append(" PAUSED ", style="bold black on yellow")
            row.append("   ")
            row.append_text(self._keycap("p", "resume", accent="yellow"))
        else:
            row.append_text(self._keycap("p", "pause", accent=ACCENT))
        sep = Text("    •    ", style="grey37")
        row.append_text(sep.copy())
        row.append_text(self._keycap("s", "skip current", accent=ACCENT))
        row.append_text(sep.copy())
        row.append_text(self._keycap("q", "quit gracefully", accent=ACCENT))
        row.append_text(sep.copy())
        row.append_text(self._keycap("^C", "abort now", accent="grey70"))
        return Panel(
            Align.center(row),
            title="[bold]Keys[/bold]",
            title_align="left",
            border_style=ACCENT,
            padding=(0, 1),
        )

    # -- refresh / run --------------------------------------------------------
    def _refresh(self) -> None:
        self._layout["header"].update(self._render_header())
        self._layout["providers"].update(self._render_providers())
        self._layout["current"].update(self._render_current())
        self._layout["progress"].update(self._render_progress())
        self._layout["recent"].update(self._render_recent())
        self._layout["footer"].update(self._render_footer())

    def __rich__(self) -> Layout:
        """Make the dashboard the Live renderable directly.

        Rebuilt on every ``Live.refresh()``. Those refreshes are driven only
        from the asyncio thread — by ``_animate`` on a timer and by the event
        loop after each event — never by a Rich background thread (Live is
        created with ``auto_refresh=False``). That keeps ``_refresh`` on the
        same thread that mutates the state it reads, so they never race. When
        the view is soft-frozen via the [p] hotkey we skip the rebuild and
        return the last frame, leaving it static to read.
        """
        if not self._view_frozen:
            self._refresh()
        return self._layout

    def _live_active(self) -> bool:
        return (
            self._live is not None
            and self._live.is_started
            and self.paused.is_set()
            and not self._view_frozen
        )

    async def _animate(self) -> None:
        """Steady ~8 fps repaint so the clock, spinner, and progress bar move
        between events. Runs on the asyncio thread (not a Rich refresh thread),
        so it can't race ``_apply``'s mutations of the state ``_refresh`` reads."""
        try:
            while True:
                await asyncio.sleep(0.125)
                if self._live_active():
                    try:
                        self._live.refresh()  # type: ignore[union-attr]
                    except Exception:
                        pass
        except asyncio.CancelledError:
            pass

    async def run(self, bus: EventBus, events: AsyncIterator[StepEvent] | None = None) -> None:
        # Subscribe synchronously at call time if a stream wasn't pre-supplied.
        # The caller can pass ``bus.subscribe()`` created *before* scheduling
        # this task to guarantee no early events are missed (fan-out drops
        # events emitted before a subscriber registers).
        stream = events if events is not None else bus.subscribe()
        self._refresh()
        # auto_refresh=False: never spin up Rich's background refresh thread, so
        # __rich__/_refresh only runs on this asyncio thread (see _animate).
        self._live = Live(
            self, console=self.console, refresh_per_second=8, screen=False, auto_refresh=False
        )
        self._live.start()
        try:
            self._live.refresh()  # paint the first frame
        except Exception:
            pass
        ticker = asyncio.create_task(self._animate())
        try:
            async for event in stream:
                self._apply(event)
                # Immediate repaint so the change shows without waiting for the
                # next animation tick. Same thread as _animate — never concurrent.
                if self._live_active():
                    try:
                        self._live.refresh()
                    except Exception:
                        pass
        finally:
            ticker.cancel()
            try:
                await ticker
            except asyncio.CancelledError:
                pass
            if self._live is not None and self._live.is_started:
                # Paint the final state before tearing Live down.
                try:
                    self._view_frozen = False
                    self._live.refresh()
                except Exception:
                    pass
                self._live.stop()

    def _log(self, kind: EventKind, slug: str, message: str) -> None:
        icon, style = _LOG_STYLE.get(kind, ("·", _MUTED))
        prefix = f"[{slug}] " if slug else ""
        self.recent.append((icon, style, f"{prefix}{message}"))

    def _apply(self, event: StepEvent) -> None:
        slug = event.provider_slug
        if event.kind == EventKind.START:
            self.current_slug = slug
            self.current_step = "starting"
            self.prompt_active = None
            self.statuses[slug] = "running"
            self._log(event.kind, slug, "start")
        elif event.kind == EventKind.STEP:
            self.current_step = event.message
            self._log(event.kind, slug, event.message)
        elif event.kind == EventKind.LOG:
            self._log(event.kind, slug, event.message)
        elif event.kind == EventKind.SUCCESS:
            self.statuses[slug] = "done"
            self.prompt_active = None
            key = event.payload.get("api_key") or ""
            if key:
                self.keys_preview[slug] = f"{key[:4]}…{key[-4:]}"
            done = sum(1 for v in self.statuses.values() if v == "done")
            self._progress.update(self._task_id, completed=done)
            self._log(event.kind, slug, "key captured")
        elif event.kind == EventKind.SKIP:
            self.statuses[slug] = "skipped"
            self.prompt_active = None
            self.notes[slug] = event.message[:40]
            self._log(event.kind, slug, f"skipped: {event.message}")
        elif event.kind == EventKind.FAIL:
            self.statuses[slug] = "failed"
            self.prompt_active = None
            self.notes[slug] = event.message[:40]
            self._log(event.kind, slug, event.message)
        elif event.kind == EventKind.RETRY:
            self.retries += 1
            self.current_step = "retrying…"
            self.prompt_active = None
            self._log(event.kind, slug, event.message)
        elif event.kind == EventKind.AI_CALL:
            self.ai_calls += 1
            self._log(event.kind, "ai", event.message)
        elif event.kind == EventKind.PROMPT:
            self.prompt_active = event.message
            self._log(event.kind, "prompt", event.message)
        elif event.kind == EventKind.DASHBOARD_PAUSE:
            # Soft view-freeze from the [p] hotkey. Must NOT touch Live here —
            # the run loop simply stops refreshing, leaving the last frame up.
            self._view_frozen = True
            self._log(EventKind.LOG, "", "view paused")
        elif event.kind == EventKind.DASHBOARD_RESUME:
            self._view_frozen = False
            self._log(EventKind.LOG, "", "view resumed")

    async def pause(self) -> None:
        """Called by InteractiveManager before reading from stdin. Idempotent."""
        self.paused.clear()
        if self._live is not None and self._live.is_started:
            try:
                self._live.stop()
            except Exception:
                pass

    async def resume(self) -> None:
        """Called by InteractiveManager after stdin read returns. Idempotent."""
        self.paused.set()
        if self._live is not None and not self._live.is_started:
            try:
                self._live.start()
            except Exception:
                pass
