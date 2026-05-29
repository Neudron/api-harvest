from __future__ import annotations

from pathlib import Path

from harvest.models import HarvestResult
from harvest.parser import build_run_order, parse_providers_md
from harvest.state import StateStore, plan_run, resume_filter

ROOT = Path(__file__).resolve().parent.parent


def test_state_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "state.json"
    store = StateStore(p)
    store.load()
    store.mark(
        HarvestResult(
            provider_slug="groq",
            provider_name="Groq",
            tier=1,
            status="done",
            api_key="gsk_test",
            env_var="GROQ_API_KEY",
        )
    )
    store2 = StateStore(p)
    state2 = store2.load()
    assert "groq" in state2.results
    assert state2.results["groq"].status == "done"
    assert state2.results["groq"].api_key == "gsk_test"


def test_reset_one(tmp_path: Path) -> None:
    p = tmp_path / "state.json"
    store = StateStore(p)
    store.load()
    for slug in ("groq", "cerebras"):
        store.mark(
            HarvestResult(
                provider_slug=slug,
                provider_name=slug,
                tier=1,
                status="done",
            )
        )
    assert store.reset("groq") == 1
    assert "groq" not in store.state.results
    assert "cerebras" in store.state.results


def test_reset_all(tmp_path: Path) -> None:
    p = tmp_path / "state.json"
    store = StateStore(p)
    store.load()
    store.mark(HarvestResult(provider_slug="groq", provider_name="Groq", tier=1, status="done"))
    assert store.reset(None) == 1
    assert store.state.results == {}


def test_resume_filter(tmp_path: Path) -> None:
    p = tmp_path / "state.json"
    store = StateStore(p)
    store.load()
    store.mark(HarvestResult(provider_slug="groq", provider_name="Groq", tier=1, status="done"))
    store.mark(
        HarvestResult(
            provider_slug="anthropic",
            provider_name="Anthropic",
            tier=2,
            status="skipped",
            user_skipped=True,
        )
    )
    store.mark(
        HarvestResult(
            provider_slug="cerebras",
            provider_name="Cerebras",
            tier=1,
            status="failed",
        )
    )

    specs = parse_providers_md(ROOT / "providers.md")
    to_run, handled = resume_filter(specs, store.state)
    handled_slugs = {s.slug for s in handled}
    to_run_slugs = {s.slug for s in to_run}
    assert "groq" in handled_slugs
    assert "anthropic" in handled_slugs
    assert "cerebras" in to_run_slugs  # failed → retried


def test_plan_run_dispositions(tmp_path: Path) -> None:
    p = tmp_path / "state.json"
    store = StateStore(p)
    store.load()
    store.mark(HarvestResult(provider_slug="groq", provider_name="Groq", tier=1, status="done"))
    store.mark(
        HarvestResult(
            provider_slug="anthropic",
            provider_name="Anthropic",
            tier=2,
            status="skipped",
            user_skipped=True,
        )
    )

    specs = build_run_order(parse_providers_md(ROOT / "providers.md"))
    disp = dict((spec.slug, reason) for spec, reason in plan_run(specs, store.state))
    assert disp["groq"] == "skip (already done)"
    assert disp["anthropic"] == "skip (user-skipped)"
    assert disp["cerebras"] == "run"  # untouched → runs


def test_plan_run_only_and_skip(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.json")
    store.load()
    specs = build_run_order(parse_providers_md(ROOT / "providers.md"))

    only = dict((s.slug, r) for s, r in plan_run(specs, store.state, only={"groq"}))
    assert only["groq"] == "run"
    assert only["cerebras"] == "excluded (--only)"

    skipped = dict((s.slug, r) for s, r in plan_run(specs, store.state, skip={"groq"}))
    assert skipped["groq"] == "excluded (--skip)"
    assert skipped["cerebras"] == "run"
