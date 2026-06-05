from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from harvest import config
from harvest.parser import build_run_order, parse_providers_md
from harvest.state import StateStore

app = typer.Typer(
    add_completion=True,
    help="api-harvest: automate signup at AI providers and harvest API keys.",
)
console = Console()


def _version_string() -> str:
    """Resolve the installed version, falling back to the package attribute for
    editable/unpacked checkouts where distribution metadata may be absent."""
    try:
        from importlib.metadata import PackageNotFoundError, version

        try:
            return version("api-harvest")
        except PackageNotFoundError:
            pass
    except Exception:  # pragma: no cover - importlib always present on 3.11+
        pass
    from harvest import __version__

    return __version__


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"api-harvest {_version_string()}")
        raise typer.Exit()


def _complete_slug(incomplete: str) -> list[str]:
    """Shell-completion for provider slugs (used by --only/--skip and reset)."""
    try:
        specs = build_run_order(parse_providers_md(config.PROVIDERS_MD))
    except Exception:
        return []
    return [s.slug for s in specs if s.slug.startswith(incomplete)]


@app.callback()
def _main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show the api-harvest version and exit.",
        ),
    ] = False,
) -> None:
    """api-harvest: automate signup at AI providers and harvest API keys."""


@app.command()
def version() -> None:
    """Print the installed api-harvest version."""
    console.print(f"api-harvest {_version_string()}")


@app.command()
def doctor() -> None:
    """Run preflight checks (catalog, outputs, keys, browser deps)."""
    from harvest.doctor import run_checks

    checks = run_checks()
    table = Table(title="api-harvest doctor")
    table.add_column("Check")
    table.add_column("OK", width=3)
    table.add_column("Detail")
    for name, ok, detail in checks:
        badge = "[green]✓[/green]" if ok else "[red]✗[/red]"
        table.add_row(name, badge, detail)
    console.print(table)
    if not all(ok for _, ok, _ in checks):
        raise typer.Exit(code=1)


@app.command(name="list")
def list_providers() -> None:
    """Print the providers parsed from providers.md."""
    specs = build_run_order(parse_providers_md(config.PROVIDERS_MD))
    table = Table(title=f"{len(specs)} providers")
    table.add_column("#", width=3)
    table.add_column("Slug")
    table.add_column("Name")
    table.add_column("Tier", width=4)
    table.add_column("CC")
    table.add_column("Phone")
    table.add_column("Env Var")
    for i, s in enumerate(specs, 1):
        table.add_row(
            str(i),
            s.slug,
            s.name,
            f"T{s.tier}",
            "yes" if s.requires_cc else "no",
            "yes" if s.requires_phone else "no",
            s.env_var or "—",
        )
    console.print(table)


@app.command()
def status() -> None:
    """Show current state.json contents."""
    config.ensure_dirs()
    store = StateStore(config.STATE_PATH)
    state = store.load()
    table = Table(title=f"state.json: {len(state.results)} entries")
    table.add_column("Slug")
    table.add_column("Status")
    table.add_column("Env Var")
    table.add_column("Key (last 4)")
    table.add_column("Note")
    for slug, r in sorted(state.results.items()):
        key = r.api_key or ""
        tail = f"…{key[-4:]}" if key else "—"
        table.add_row(slug, r.status, r.env_var or "—", tail, (r.notes or r.error or "")[:50])
    console.print(table)
    console.print(f"AI rescue calls used so far: [bold]{state.ai_budget_used}[/bold]")


@app.command(name="ai-log")
def ai_log() -> None:
    """Summarize the AI selector-rescue audit log (ai_calls.jsonl)."""
    from harvest.ai.audit import load_records, summarize

    records = load_records(config.AI_LOG_PATH)
    summary = summarize(records)
    if summary.total_calls == 0:
        console.print("No AI rescue calls recorded yet.")
        return

    console.print(
        f"AI rescue calls: [bold]{summary.total_calls}[/bold] "
        f"({summary.successes} ok, {summary.errors} errors, "
        f"{summary.error_rate:.0%} error rate)"
    )
    table = Table(title="AI rescue calls per provider")
    table.add_column("Provider")
    table.add_column("Calls", justify="right")
    table.add_column("Confident suggestion")
    for provider, count in sorted(summary.per_provider.items(), key=lambda kv: (-kv[1], kv[0])):
        confident = "yes" if provider in summary.confident_providers else "—"
        table.add_row(provider, str(count), confident)
    console.print(table)


@app.command()
def reset(
    provider: str | None = typer.Argument(
        None, help="Slug, or omit to clear all", autocompletion=_complete_slug
    ),
) -> None:
    config.ensure_dirs()
    store = StateStore(config.STATE_PATH)
    store.load()
    n = store.reset(provider)
    console.print(f"Cleared {n} entr{'y' if n == 1 else 'ies'} from state.")


@app.command()
def export(
    format: str = typer.Option("all", "--format", "-f", help="env|json|md|all"),
) -> None:
    """Re-render outputs from keys.json without running automation."""
    config.ensure_dirs()
    from harvest.output import rerender

    fmt = format.lower().strip()
    if fmt == "all":
        formats = {"env", "md", "json"}
    elif fmt in ("env", "md", "json"):
        formats = {fmt}
    else:
        console.print(f"[red]Unknown --format {format!r}; use env|json|md|all[/red]")
        raise typer.Exit(code=2)

    n = rerender(config.JSON_PATH, config.ENV_PATH, config.MD_PATH, formats=formats)
    console.print(f"Re-rendered {sorted(formats)} from {n} stored results.")


@app.command(name="validate")
def validate_keys(
    only: Annotated[str | None, typer.Option("--only", help="Comma-separated slugs to include", autocompletion=_complete_slug)] = None,
    skip: Annotated[str | None, typer.Option("--skip", help="Comma-separated slugs to skip", autocompletion=_complete_slug)] = None,
) -> None:
    """Probe harvested keys (from keys.json) against each provider's API.

    Records the outcome back into keys.json / keys.md and exits non-zero if any
    captured key fails to authenticate.
    """
    config.ensure_dirs()
    from harvest.output import load_results, update_validation
    from harvest.validate import iso_now, validate_key

    only_set = {s.strip() for s in only.split(",")} if only else None
    skip_set = {s.strip() for s in skip.split(",")} if skip else None

    rows = load_results(config.JSON_PATH)
    rows = [r for r in rows if r.get("api_key")]
    if only_set:
        rows = [r for r in rows if r.get("provider_slug") in only_set]
    if skip_set:
        rows = [r for r in rows if r.get("provider_slug") not in skip_set]

    if not rows:
        console.print("[yellow]No harvested keys to validate (keys.json is empty).[/yellow]")
        return

    table = Table(title="Key validation")
    table.add_column("Provider")
    table.add_column("Result")
    table.add_column("HTTP")
    table.add_column("Latency")
    table.add_column("Detail")

    _styles = {"valid": "green", "invalid": "red", "unsupported": "dim", "error": "yellow"}
    invalid = 0
    for r in rows:
        slug = r.get("provider_slug", "")
        outcome = validate_key(slug, r.get("api_key"))
        update_validation(
            slug,
            validation_status=outcome.status,
            validation_detail=outcome.detail,
            validated_at=iso_now(),
            json_path=config.JSON_PATH,
            md_path=config.MD_PATH,
        )
        if outcome.status == "invalid":
            invalid += 1
        style = _styles.get(outcome.status, "white")
        latency = f"{outcome.latency_ms}ms" if outcome.latency_ms is not None else "—"
        http = str(outcome.http_status) if outcome.http_status is not None else "—"
        table.add_row(
            r.get("provider_name", slug),
            f"[{style}]{outcome.status}[/{style}]",
            http,
            latency,
            outcome.detail,
        )

    console.print(table)
    if invalid:
        console.print(f"[red]{invalid} key(s) failed validation.[/red]")
        raise typer.Exit(code=1)


@app.command()
def report() -> None:
    """Write a run summary (outputs/report.md) from keys.json."""
    config.ensure_dirs()
    from harvest.report import build_report

    report_path = config.OUTPUTS_DIR / "report.md"
    n = build_report(config.JSON_PATH, report_path)
    console.print(f"Wrote run summary for {n} providers to {report_path}")


@app.command()
def run(
    cdp_port: Annotated[int | None, typer.Option("--cdp-port", help="Attach to running Chrome via CDP")] = None,
    profile_dir: Annotated[Path | None, typer.Option("--profile-dir", help="Use a dedicated Chromium profile dir")] = None,
    only: Annotated[str | None, typer.Option("--only", help="Comma-separated slugs to include", autocompletion=_complete_slug)] = None,
    skip: Annotated[str | None, typer.Option("--skip", help="Comma-separated slugs to skip", autocompletion=_complete_slug)] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show the resolved run plan and exit without launching a browser")] = False,
    no_dashboard: Annotated[bool, typer.Option("--no-dashboard", help="Disable Rich Live dashboard")] = False,
    validate: Annotated[bool, typer.Option("--validate/--no-validate", help="Probe each captured key against its provider API to confirm it works")] = False,
    ai_model: Annotated[str, typer.Option("--ai-model")] = config.DEFAULT_AI_MODEL,
    ai_budget: Annotated[int, typer.Option("--ai-budget")] = config.DEFAULT_AI_BUDGET_PER_RUN,
    gemini_key: Annotated[str | None, typer.Option("--gemini-key", help="Bootstrap Gemini key (skips AI Studio rescue)")] = None,
) -> None:
    """Run the harvest pipeline."""
    only_set = {s.strip() for s in only.split(",")} if only else None
    skip_set = {s.strip() for s in skip.split(",")} if skip else None

    if dry_run:
        from harvest.state import plan_run

        config.ensure_dirs()
        specs = build_run_order(parse_providers_md(config.PROVIDERS_MD))
        store = StateStore(config.STATE_PATH)
        store.load()
        plan = plan_run(specs, store.state, only_set, skip_set)
        table = Table(title="Run plan (dry run — no browser launched)")
        table.add_column("#", width=3)
        table.add_column("Slug")
        table.add_column("Disposition")
        will_run = 0
        for i, (spec, disp) in enumerate(plan, 1):
            if disp == "run":
                will_run += 1
                style = "[green]run[/green]"
            else:
                style = f"[dim]{disp}[/dim]"
            table.add_row(str(i), spec.slug, style)
        console.print(table)
        console.print(f"[bold]{will_run}[/bold] of {len(plan)} providers would run.")
        return

    if cdp_port is not None and profile_dir is not None:
        console.print(
            "[red]--cdp-port and --profile-dir are mutually exclusive. Pick one.[/red]"
        )
        raise typer.Exit(code=2)
    if cdp_port is None and profile_dir is None:
        console.print(
            "[red]Provide a browser mode:[/red]\n"
            "  --cdp-port 9222            (attach to an existing Chrome started with --remote-debugging-port)\n"
            "  --profile-dir ./harvest-chrome  (use a dedicated Chromium profile)"
        )
        raise typer.Exit(code=2)

    config.ensure_dirs()

    gemini = gemini_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_GENERATIVE_AI_API_KEY")

    try:
        asyncio.run(
            _run_async(
                cdp_port=cdp_port,
                profile_dir=profile_dir,
                only_set=only_set,
                skip_set=skip_set,
                no_dashboard=no_dashboard,
                validate=validate,
                ai_model=ai_model,
                ai_budget=ai_budget,
                gemini_key=gemini,
            )
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user. State has been saved.[/yellow]")
        raise typer.Exit(code=130) from None


async def _run_async(
    *,
    cdp_port: int | None,
    profile_dir: Path | None,
    only_set: set[str] | None,
    skip_set: set[str] | None,
    no_dashboard: bool,
    validate: bool,
    ai_model: str,
    ai_budget: int,
    gemini_key: str | None,
) -> None:
    from harvest.browser import close_browser, open_browser
    from harvest.dashboard import Dashboard
    from harvest.events import EventBus, JsonlEventSink
    from harvest.hotkeys import HotkeyState, run_hotkey_listener
    from harvest.interactive import InteractiveManager
    from harvest.orchestrator import RunOptions, run_pipeline

    specs = build_run_order(parse_providers_md(config.PROVIDERS_MD))
    store = StateStore(config.STATE_PATH)
    store.load()

    bus = EventBus()
    dashboard = Dashboard(console, specs) if not no_dashboard else None
    interactive = InteractiveManager(dashboard, console)
    hotkeys = HotkeyState()

    handle = await open_browser(cdp_port=cdp_port, profile_dir=profile_dir)

    # Register subscriptions synchronously *before* scheduling tasks so no early
    # events are missed (fan-out only delivers to subscribers present at emit time).
    dashboard_task = None
    if dashboard is not None:
        dash_stream = bus.subscribe()
        dashboard_task = asyncio.create_task(dashboard.run(bus, events=dash_stream))

    # JSONL audit sink: every event recorded to .harvest/events.jsonl for reporting.
    sink = JsonlEventSink(config.RUNTIME_DIR / "events.jsonl")
    sink_stream = bus.subscribe()
    sink_task = asyncio.create_task(sink.run(bus, events=sink_stream))

    hotkey_task = asyncio.create_task(run_hotkey_listener(hotkeys, bus))

    options = RunOptions(
        only=only_set,
        skip=skip_set,
        ai_model=ai_model,
        ai_budget=ai_budget,
        gemini_api_key=gemini_key,
        hotkeys=hotkeys,
        validate=validate,
    )

    interrupted = False
    try:
        await run_pipeline(
            specs=specs,
            handle=handle,
            state_store=store,
            bus=bus,
            interactive=interactive,
            options=options,
        )
    except (KeyboardInterrupt, asyncio.CancelledError):
        interrupted = True
    finally:
        await bus.close()
        if dashboard_task is not None:
            try:
                await asyncio.wait_for(dashboard_task, timeout=2.0)
            except TimeoutError:
                dashboard_task.cancel()
        try:
            await asyncio.wait_for(sink_task, timeout=2.0)
        except TimeoutError:
            sink_task.cancel()
        hotkey_task.cancel()
        try:
            await asyncio.wait_for(hotkey_task, timeout=1.0)
        except (TimeoutError, asyncio.CancelledError):
            pass
        await close_browser(handle)
        if interrupted:
            # Re-raise so the outer typer handler exits 130 with the user message.
            raise KeyboardInterrupt

    # Final summary
    state = store.state
    done = sum(1 for r in state.results.values() if r.status == "done")
    failed = sum(1 for r in state.results.values() if r.status == "failed")
    skipped = sum(1 for r in state.results.values() if r.status == "skipped")
    console.print(
        f"\n[bold cyan]Done.[/bold cyan]  "
        f"[green]captured={done}[/green]  "
        f"[red]failed={failed}[/red]  "
        f"[yellow]skipped={skipped}[/yellow]  "
        f"out of {len(specs)} providers."
    )
    console.print(f"Outputs: {config.ENV_PATH}, {config.JSON_PATH}, {config.MD_PATH}")


if __name__ == "__main__":
    app()
