"""Drive Dashboard._apply with synthetic events; assert state transitions
without touching Rich Live."""

from __future__ import annotations

from rich.console import Console

from harvest.dashboard import Dashboard
from harvest.models import EventKind, ProviderSpec, StepEvent


def _spec(slug: str, tier: int = 1) -> ProviderSpec:
    return ProviderSpec(
        slug=slug,
        name=slug.title(),
        tier=tier,  # type: ignore[arg-type]
        order_index=0,
        signup_url="https://example.com",
        api_key_url="https://example.com",
        env_var=f"{slug.upper()}_API_KEY",
        requires_cc=False,
        requires_phone=False,
        rate_limits="",
        free_models=[],
        gotchas="",
        raw_section="",
    )


def _dash() -> Dashboard:
    return Dashboard(Console(record=True), [_spec("groq"), _spec("cerebras")])


def test_start_marks_running() -> None:
    d = _dash()
    d._apply(StepEvent(provider_slug="groq", kind=EventKind.START, message="start"))
    assert d.statuses["groq"] == "running"
    assert d.current_slug == "groq"
    assert d._counts()["running"] == 1


def test_success_marks_done_and_records_preview() -> None:
    d = _dash()
    d._apply(StepEvent(provider_slug="groq", kind=EventKind.START))
    d._apply(
        StepEvent(
            provider_slug="groq",
            kind=EventKind.SUCCESS,
            message="captured",
            payload={"api_key": "gsk_abcdef12345678"},
        )
    )
    assert d.statuses["groq"] == "done"
    assert d.keys_preview["groq"].startswith("gsk_")
    assert d._counts()["done"] == 1


def test_skip_marks_skipped() -> None:
    d = _dash()
    d._apply(StepEvent(provider_slug="cerebras", kind=EventKind.SKIP, message="user skipped"))
    assert d.statuses["cerebras"] == "skipped"
    assert "user skipped" in d.notes["cerebras"]


def test_fail_marks_failed() -> None:
    d = _dash()
    d._apply(StepEvent(provider_slug="groq", kind=EventKind.FAIL, message="oops"))
    assert d.statuses["groq"] == "failed"


def test_pause_resume_events_are_ignored_in_apply() -> None:
    """Pause/resume from _apply must never touch Live (only the public methods do).
    Regression test for the Wave 1 fix — _live stays None and nothing raises."""
    d = _dash()
    assert d._live is None
    d._apply(StepEvent(provider_slug="", kind=EventKind.DASHBOARD_PAUSE))
    d._apply(StepEvent(provider_slug="", kind=EventKind.DASHBOARD_RESUME))
    assert d._live is None


def test_pause_event_freezes_view_without_touching_live() -> None:
    """The [p] hotkey emits DASHBOARD_PAUSE; _apply soft-freezes the view."""
    d = _dash()
    assert d._view_frozen is False
    d._apply(StepEvent(provider_slug="", kind=EventKind.DASHBOARD_PAUSE))
    assert d._view_frozen is True
    d._apply(StepEvent(provider_slug="", kind=EventKind.DASHBOARD_RESUME))
    assert d._view_frozen is False


def test_retry_event_increments_counter_and_logs() -> None:
    d = _dash()
    d._apply(StepEvent(provider_slug="groq", kind=EventKind.START))
    d._apply(StepEvent(provider_slug="groq", kind=EventKind.RETRY, message="attempt 1 failed; retrying"))
    assert d.retries == 1
    assert d.current_step == "retrying…"


def test_ai_call_event_increments_counter() -> None:
    d = _dash()
    d._apply(StepEvent(provider_slug="", kind=EventKind.AI_CALL, message="rescued selector"))
    d._apply(StepEvent(provider_slug="", kind=EventKind.AI_CALL, message="rescued selector"))
    assert d.ai_calls == 2


def test_prompt_event_sets_then_clears_on_resolution() -> None:
    d = _dash()
    d._apply(StepEvent(provider_slug="groq", kind=EventKind.START))
    d._apply(StepEvent(provider_slug="groq", kind=EventKind.PROMPT, message="Enter SMS code"))
    assert d.prompt_active == "Enter SMS code"
    # Any terminal status for the provider clears the active prompt.
    d._apply(StepEvent(provider_slug="groq", kind=EventKind.SUCCESS, payload={"api_key": "gsk_xxxx1234"}))
    assert d.prompt_active is None


def test_fmt_elapsed_formats() -> None:
    assert Dashboard._fmt_elapsed(0) == "00:00"
    assert Dashboard._fmt_elapsed(75) == "01:15"
    assert Dashboard._fmt_elapsed(3661) == "1:01:01"


def test_refresh_and_rich_render_do_not_raise() -> None:
    """Every render component must compose into the layout without error,
    across a representative mix of statuses."""
    d = _dash()
    d._apply(StepEvent(provider_slug="groq", kind=EventKind.START))
    d._apply(StepEvent(provider_slug="groq", kind=EventKind.PROMPT, message="Enter SMS code"))
    d._apply(StepEvent(provider_slug="cerebras", kind=EventKind.FAIL, message="boom"))
    d._apply(StepEvent(provider_slug="", kind=EventKind.AI_CALL, message="rescue"))
    # __rich__ drives _refresh; render it to a recording console.
    console = Console(record=True, width=120, height=40)
    console.print(d.__rich__())
    out = console.export_text()
    assert "api-harvest" in out
    assert "Providers" in out
    assert "Keys" in out  # footer keybinding panel present
