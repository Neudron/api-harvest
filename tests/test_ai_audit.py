"""Tests for harvest.ai.audit aggregation (offline)."""

from __future__ import annotations

import json
from pathlib import Path

from harvest.ai.audit import load_records, summarize


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")


def test_summarize_empty() -> None:
    s = summarize([])
    assert s.total_calls == 0
    assert s.successes == 0
    assert s.errors == 0
    assert s.error_rate == 0.0
    assert s.per_provider == {}


def test_summarize_counts_per_provider() -> None:
    records = [
        {"provider": "groq", "suggestion": {"confidence": 0.9}},
        {"provider": "groq", "suggestion": {"confidence": 0.2}},
        {"provider": "cohere", "suggestion": {"confidence": 0.7}},
    ]
    s = summarize(records)
    assert s.total_calls == 3
    assert s.per_provider == {"groq": 2, "cohere": 1}


def test_summarize_errors_and_rate() -> None:
    records = [
        {"provider": "groq", "suggestion": {"confidence": 0.9}},
        {"provider": "groq", "error": "boom"},
        {"provider": "cohere", "error": "nope"},
    ]
    s = summarize(records)
    assert s.total_calls == 3
    assert s.errors == 2
    assert s.successes == 1
    assert abs(s.error_rate - 2 / 3) < 1e-9


def test_summarize_confident_providers_threshold() -> None:
    records = [
        {"provider": "groq", "suggestion": {"confidence": 0.9}},
        {"provider": "cohere", "suggestion": {"confidence": 0.4}},
    ]
    s = summarize(records, confidence_threshold=0.5)
    assert "groq" in s.confident_providers
    assert "cohere" not in s.confident_providers


def test_summarize_handles_missing_fields() -> None:
    records = [{}, {"suggestion": "not-a-dict"}, {"provider": "x"}]
    s = summarize(records)
    assert s.total_calls == 3
    assert s.per_provider["unknown"] == 2  # two records had no provider
    assert s.per_provider["x"] == 1


def test_load_records_skips_corrupt_lines(tmp_path: Path) -> None:
    path = tmp_path / "ai_calls.jsonl"
    path.write_text(
        '{"provider": "groq"}\n'
        "not json at all\n"
        "\n"
        '{"provider": "cohere", "error": "x"}\n',
        encoding="utf-8",
    )
    records = load_records(path)
    assert len(records) == 2
    assert records[0]["provider"] == "groq"
    assert records[1]["error"] == "x"


def test_load_records_missing_file(tmp_path: Path) -> None:
    assert load_records(tmp_path / "nope.jsonl") == []


def test_round_trip_from_file(tmp_path: Path) -> None:
    path = tmp_path / "ai_calls.jsonl"
    _write_jsonl(
        path,
        [
            {"provider": "groq", "suggestion": {"confidence": 0.95}},
            {"provider": "groq", "error": "timeout"},
            {"provider": "nebius", "suggestion": {"confidence": 0.6}},
        ],
    )
    s = summarize(load_records(path))
    assert s.total_calls == 3
    assert s.errors == 1
    assert s.per_provider == {"groq": 2, "nebius": 1}
    assert s.confident_providers == {"groq", "nebius"}
