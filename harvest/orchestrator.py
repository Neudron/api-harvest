from __future__ import annotations

import asyncio
import traceback
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from harvest import config
from harvest.browser import BrowserHandle, new_page
from harvest.events import EventBus
from harvest.handlers import HANDLER_REGISTRY
from harvest.handlers.recipes import GoogleSsoCreateKeyRecipe
from harvest.models import EventKind, HarvestResult, ProviderSpec, StepEvent
from harvest.output import append_result
from harvest.state import StateStore

if TYPE_CHECKING:
    from harvest.ai_assistant import AIAssistant
    from harvest.interactive import InteractiveManager


@dataclass
class RunOptions:
    only: set[str] | None = None
    skip: set[str] | None = None
    ai_model: str = config.DEFAULT_AI_MODEL
    ai_budget: int = config.DEFAULT_AI_BUDGET_PER_RUN
    gemini_api_key: str | None = None
    hotkeys: object | None = None  # HotkeyState or None


def _build_handler(spec: ProviderSpec, ai: AIAssistant | None, interactive: InteractiveManager, bus: EventBus):
    cls = HANDLER_REGISTRY.get(spec.slug)
    if cls is None:
        # Fallback: try a generic Google-SSO recipe
        return GoogleSsoCreateKeyRecipe(spec=spec, ai=ai, interactive=interactive, bus=bus)
    return cls(spec=spec, ai=ai, interactive=interactive, bus=bus)


async def run_pipeline(
    *,
    specs: list[ProviderSpec],
    handle: BrowserHandle,
    state_store: StateStore,
    bus: EventBus,
    interactive: InteractiveManager,
    options: RunOptions,
) -> None:
    """Sequentially run providers. Google AI Studio first; on success bootstrap AIAssistant."""
    ai: AIAssistant | None = None
    if options.gemini_api_key:
        from harvest.ai import GeminiBackend
        from harvest.ai_assistant import AIAssistant

        backend = GeminiBackend(api_key=options.gemini_api_key, model=options.ai_model)
        ai = AIAssistant(
            backend=backend,
            log_path=config.AI_LOG_PATH,
            per_run_budget=options.ai_budget,
        )

    for spec in specs:
        hk = options.hotkeys
        if hk is not None and getattr(hk, "quit_requested", False):
            await bus.emit(
                StepEvent(provider_slug=spec.slug, kind=EventKind.LOG, message="quit hotkey received")
            )
            break
        if hk is not None and getattr(hk, "skip_requested", False):
            # Consume the request and skip this single provider.
            hk.skip_requested = False
            result = HarvestResult(
                provider_slug=spec.slug,
                provider_name=spec.name,
                tier=spec.tier,
                status="skipped",
                env_var=spec.env_var,
                dashboard_url=spec.api_key_url,
                rate_limits=spec.rate_limits,
                user_skipped=True,
                notes="skipped via hotkey",
            )
            state_store.mark(result)
            append_result(result, env_path=config.ENV_PATH, json_path=config.JSON_PATH, md_path=config.MD_PATH)
            await bus.emit(StepEvent(provider_slug=spec.slug, kind=EventKind.SKIP, message="hotkey"))
            continue
        if options.only and spec.slug not in options.only:
            continue
        if options.skip and spec.slug in options.skip:
            continue
        prev = state_store.state.results.get(spec.slug)
        if prev and (prev.status == "done" or prev.user_skipped):
            await bus.emit(
                StepEvent(
                    provider_slug=spec.slug,
                    kind=EventKind.LOG,
                    message=f"skipping (already {prev.status})",
                )
            )
            continue

        await bus.emit(StepEvent(provider_slug=spec.slug, kind=EventKind.START, message="start"))

        # CC pause upfront
        if spec.requires_cc and spec.slug not in ("azure-openai",):
            choice = await interactive.pause_for_cc(
                spec.name, "Credit card required at signup (per providers.md)."
            )
            if choice == "skip":
                result = HarvestResult(
                    provider_slug=spec.slug,
                    provider_name=spec.name,
                    tier=spec.tier,
                    status="skipped",
                    env_var=spec.env_var,
                    dashboard_url=spec.api_key_url,
                    rate_limits=spec.rate_limits,
                    user_skipped=True,
                    notes="CC required; user declined",
                )
                state_store.mark(result)
                append_result(result, env_path=config.ENV_PATH, json_path=config.JSON_PATH, md_path=config.MD_PATH)
                await bus.emit(StepEvent(provider_slug=spec.slug, kind=EventKind.SKIP, message="CC declined"))
                continue

        page = await new_page(handle)
        try:
            handler = _build_handler(spec, ai, interactive, bus)
            try:
                result = await handler.run(page)
            except (asyncio.CancelledError, KeyboardInterrupt):
                # Mark the in-flight provider as user_skipped so it isn't retried
                # on the next run, then re-raise so the caller can clean up.
                result = HarvestResult(
                    provider_slug=spec.slug,
                    provider_name=spec.name,
                    tier=spec.tier,
                    status="skipped",
                    env_var=spec.env_var,
                    dashboard_url=spec.api_key_url,
                    rate_limits=spec.rate_limits,
                    user_skipped=True,
                    notes="interrupted (Ctrl+C)",
                )
                state_store.mark(result)
                append_result(
                    result,
                    env_path=config.ENV_PATH,
                    json_path=config.JSON_PATH,
                    md_path=config.MD_PATH,
                )
                raise
            except Exception as e:
                # Write the full traceback to disk so debugging doesn't depend
                # on whatever truncated string we put in result.error.
                err_dir = config.RUNTIME_DIR / "errors"
                err_dir.mkdir(parents=True, exist_ok=True)
                ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
                err_path = err_dir / f"{spec.slug}-{ts}.log"
                try:
                    err_path.write_text(
                        f"Provider: {spec.slug}\nException: {type(e).__name__}: {e}\n\n"
                        + traceback.format_exc(),
                        encoding="utf-8",
                    )
                except Exception:
                    pass
                result = HarvestResult(
                    provider_slug=spec.slug,
                    provider_name=spec.name,
                    tier=spec.tier,
                    status="failed",
                    env_var=spec.env_var,
                    dashboard_url=spec.api_key_url,
                    rate_limits=spec.rate_limits,
                    error=f"{type(e).__name__}: {e} (traceback: {err_path})",
                )
        finally:
            try:
                if handle.is_cdp and page in handle.owned_pages:
                    handle.owned_pages.remove(page)
                await page.close()
            except Exception:
                pass

        state_store.mark(result)
        if ai is not None:
            state_store.state.ai_budget_used = ai.run_used
            state_store.save()
        append_result(
            result,
            env_path=config.ENV_PATH,
            json_path=config.JSON_PATH,
            md_path=config.MD_PATH,
        )

        if result.status == "done":
            await bus.emit(
                StepEvent(
                    provider_slug=spec.slug,
                    kind=EventKind.SUCCESS,
                    message="key captured",
                    payload={"api_key": result.api_key or ""},
                )
            )
            # Bootstrap AI assistant after Google AI Studio succeeds
            if spec.slug == "google-gemini-ai-studio" and ai is None and result.api_key:
                from harvest.ai import GeminiBackend
                from harvest.ai_assistant import AIAssistant

                backend = GeminiBackend(api_key=result.api_key, model=options.ai_model)
                ai = AIAssistant(
                    backend=backend,
                    log_path=config.AI_LOG_PATH,
                    per_run_budget=options.ai_budget,
                )
                await bus.emit(
                    StepEvent(
                        provider_slug=spec.slug,
                        kind=EventKind.AI_CALL,
                        message="Gemini AI assistant initialized for subsequent providers",
                    )
                )
        elif result.status == "skipped":
            await bus.emit(
                StepEvent(
                    provider_slug=spec.slug,
                    kind=EventKind.SKIP,
                    message=result.notes or "skipped",
                )
            )
        else:
            await bus.emit(
                StepEvent(
                    provider_slug=spec.slug,
                    kind=EventKind.FAIL,
                    message=result.error or "failed",
                )
            )
