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
    add_completion=False,
    help="api-harvest — automate signup at AI providers and harvest API keys.",
)
console = Console()


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
    table = Table(title=f"state.json — {len(state.results)} entries")
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


@app.command()
def reset(provider: str | None = typer.Argument(None, help="Slug, or omit to clear all")) -> None:
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

    n = rerender(config.JSON_PATH, config.ENV_PATH, config.MD_PATH)
    console.print(f"Re-rendered outputs from {n} stored results.")


@app.command()
def run(
    cdp_port: Annotated[int | None, typer.Option("--cdp-port", help="Attach to running Chrome via CDP")] = None,
    profile_dir: Annotated[Path | None, typer.Option("--profile-dir", help="Use a dedicated Chromium profile dir")] = None,
    only: Annotated[str | None, typer.Option("--only", help="Comma-separated slugs to include")] = None,
    skip: Annotated[str | None, typer.Option("--skip", help="Comma-separated slugs to skip")] = None,
    no_dashboard: Annotated[bool, typer.Option("--no-dashboard", help="Disable Rich Live dashboard")] = False,
    ai_model: Annotated[str, typer.Option("--ai-model")] = config.DEFAULT_AI_MODEL,
    ai_budget: Annotated[int, typer.Option("--ai-budget")] = config.DEFAULT_AI_BUDGET_PER_RUN,
    gemini_key: Annotated[str | None, typer.Option("--gemini-key", help="Bootstrap Gemini key (skips AI Studio rescue)")] = None,
) -> None:
    """Run the harvest pipeline."""
    if (cdp_port is None) == (profile_dir is None):
        console.print(
            "[red]Provide exactly one of --cdp-port or --profile-dir.[/red]\n"
            "  --cdp-port 9222            (attach to an existing Chrome started with --remote-debugging-port)\n"
            "  --profile-dir ./harvest-chrome  (use a dedicated Chromium profile)"
        )
        raise typer.Exit(code=2)

    config.ensure_dirs()
    only_set = {s.strip() for s in only.split(",")} if only else None
    skip_set = {s.strip() for s in skip.split(",")} if skip else None

    gemini = gemini_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_GENERATIVE_AI_API_KEY")

    asyncio.run(
        _run_async(
            cdp_port=cdp_port,
            profile_dir=profile_dir,
            only_set=only_set,
            skip_set=skip_set,
            no_dashboard=no_dashboard,
            ai_model=ai_model,
            ai_budget=ai_budget,
            gemini_key=gemini,
        )
    )


async def _run_async(
    *,
    cdp_port: int | None,
    profile_dir: Path | None,
    only_set: set[str] | None,
    skip_set: set[str] | None,
    no_dashboard: bool,
    ai_model: str,
    ai_budget: int,
    gemini_key: str | None,
) -> None:
    from harvest.browser import close_browser, open_browser
    from harvest.dashboard import Dashboard
    from harvest.events import EventBus
    from harvest.interactive import InteractiveManager
    from harvest.orchestrator import RunOptions, run_pipeline

    specs = build_run_order(parse_providers_md(config.PROVIDERS_MD))
    store = StateStore(config.STATE_PATH)
    store.load()

    bus = EventBus()
    dashboard = Dashboard(console, specs) if not no_dashboard else None
    interactive = InteractiveManager(dashboard, console)

    handle = await open_browser(cdp_port=cdp_port, profile_dir=profile_dir)

    dashboard_task = None
    if dashboard is not None:
        dashboard_task = asyncio.create_task(dashboard.run(bus))

    options = RunOptions(
        only=only_set,
        skip=skip_set,
        ai_model=ai_model,
        ai_budget=ai_budget,
        gemini_api_key=gemini_key,
    )

    try:
        await run_pipeline(
            specs=specs,
            context=handle.context,
            state_store=store,
            bus=bus,
            interactive=interactive,
            options=options,
        )
    finally:
        await bus.close()
        if dashboard_task is not None:
            try:
                await asyncio.wait_for(dashboard_task, timeout=2.0)
            except TimeoutError:
                dashboard_task.cancel()
        await close_browser(handle)

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
