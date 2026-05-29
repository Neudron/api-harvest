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
    """Pause/resume should NOT touch Live from _apply (only the public methods do).
    Regression test for the Wave 1 fix."""
    d = _dash()
    # Before the fix, the next line would call self._live.stop() on None.
    # Now it's a no-op, and the test is just that nothing raises.
    d._apply(StepEvent(provider_slug="", kind=EventKind.DASHBOARD_PAUSE))
    d._apply(StepEvent(provider_slug="", kind=EventKind.DASHBOARD_RESUME))
