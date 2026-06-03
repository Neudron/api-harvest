"""Tests for harvest.report (offline)."""

from __future__ import annotations

import json
from pathlib import Path

from harvest.report import build_report, render_report


def _r(slug: str, status: str, tier: int = 1, **kw) -> dict:
    base = {"provider_slug": slug, "provider_name": slug.title(), "tier": tier, "status": status}
    base.update(kw)
    return base


def test_render_empty() -> None:
    md = render_report([])
    assert "# Run Summary" in md
    assert "Total providers: **0**" in md
    assert "Success rate: **0%**" in md


def test_render_counts_and_rate() -> None:
    results = [
        _r("groq", "done"),
        _r("cohere", "done"),
        _r("nebius", "failed"),
        _r("modal", "skipped"),
    ]
    md = render_report(results)
    assert "Total providers: **4**" in md
    assert "Succeeded: **2**" in md
    assert "Failed: **1**" in md
    assert "Skipped: **1**" in md
    assert "Success rate: **50%**" in md


def test_render_per_tier_table() -> None:
    results = [
        _r("a", "done", tier=1),
        _r("b", "failed", tier=1),
        _r("c", "done", tier=2),
    ]
    md = render_report(results)
    assert "## Per-tier" in md
    # tier 1: 2 total, 1 done -> 50%; tier 2: 1 total, 1 done -> 100%
    assert "| 1 | 2 | 1 | 1 | 0 | 50% |" in md
    assert "| 2 | 1 | 1 | 0 | 0 | 100% |" in md


def test_render_failures_section() -> None:
    results = [
        _r("groq", "failed", error="HandlerError: button not found"),
        _r("cohere", "done"),
    ]
    md = render_report(results)
    assert "## Failures" in md
    assert "Groq" in md
    assert "button not found" in md


def test_render_failure_reason_single_line() -> None:
    results = [_r("x", "failed", error="line1\nline2\nline3")]
    md = render_report(results)
    assert "line1" in md
    assert "line2" not in md  # only first line kept


def test_build_report_writes_file(tmp_path: Path) -> None:
    json_path = tmp_path / "keys.json"
    json_path.write_text(
        json.dumps([_r("groq", "done"), _r("nebius", "failed", error="boom")]),
        encoding="utf-8",
    )
    report_path = tmp_path / "report.md"
    n = build_report(json_path, report_path)
    assert n == 2
    content = report_path.read_text()
    assert "Total providers: **2**" in content
    assert "Success rate: **50%**" in content


def test_build_report_missing_json(tmp_path: Path) -> None:
    report_path = tmp_path / "report.md"
    n = build_report(tmp_path / "nope.json", report_path)
    assert n == 0
    assert "Total providers: **0**" in report_path.read_text()


def test_build_report_corrupt_json(tmp_path: Path) -> None:
    json_path = tmp_path / "keys.json"
    json_path.write_text("not json", encoding="utf-8")
    report_path = tmp_path / "report.md"
    n = build_report(json_path, report_path)
    assert n == 0
