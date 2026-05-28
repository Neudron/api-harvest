from __future__ import annotations

import json
from pathlib import Path

from harvest.models import HarvestResult
from harvest.output import append_result, rerender


def _result(slug: str, tier: int, key: str, env: str) -> HarvestResult:
    return HarvestResult(
        provider_slug=slug,
        provider_name=slug.title(),
        tier=tier,
        status="done",
        api_key=key,
        env_var=env,
        created_at="2026-05-28T00:00:00",
        dashboard_url=f"https://{slug}.example/",
        rate_limits="30 RPM",
    )


def test_append_writes_all_three(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    json_path = tmp_path / "keys.json"
    md_path = tmp_path / "keys.md"

    append_result(
        _result("groq", 1, "gsk_abc12345", "GROQ_API_KEY"),
        env_path=env_path,
        json_path=json_path,
        md_path=md_path,
    )

    assert "GROQ_API_KEY=gsk_abc12345" in env_path.read_text()
    data = json.loads(json_path.read_text())
    assert len(data) == 1
    assert data[0]["provider_slug"] == "groq"
    md = md_path.read_text()
    assert "Groq" in md
    assert "GROQ_API_KEY" in md


def test_append_upserts_by_slug(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    json_path = tmp_path / "keys.json"
    md_path = tmp_path / "keys.md"

    append_result(
        _result("groq", 1, "gsk_oldkey", "GROQ_API_KEY"),
        env_path=env_path,
        json_path=json_path,
        md_path=md_path,
    )
    append_result(
        _result("groq", 1, "gsk_newkey", "GROQ_API_KEY"),
        env_path=env_path,
        json_path=json_path,
        md_path=md_path,
    )

    data = json.loads(json_path.read_text())
    assert len(data) == 1
    assert data[0]["api_key"] == "gsk_newkey"
    assert "gsk_newkey" in env_path.read_text()
    assert "gsk_oldkey" not in env_path.read_text()


def test_skipped_result_does_not_write_env(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    json_path = tmp_path / "keys.json"
    md_path = tmp_path / "keys.md"

    skipped = HarvestResult(
        provider_slug="anthropic",
        provider_name="Anthropic",
        tier=2,
        status="skipped",
        env_var="ANTHROPIC_API_KEY",
        user_skipped=True,
        notes="CC declined",
    )
    append_result(skipped, env_path=env_path, json_path=json_path, md_path=md_path)

    # .env should not exist or should be empty of provider keys
    if env_path.exists():
        assert "ANTHROPIC_API_KEY=" not in env_path.read_text()
    data = json.loads(json_path.read_text())
    assert len(data) == 1
    assert data[0]["status"] == "skipped"


def test_rerender_recreates_outputs(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    json_path = tmp_path / "keys.json"
    md_path = tmp_path / "keys.md"

    append_result(
        _result("groq", 1, "gsk_abc", "GROQ_API_KEY"),
        env_path=env_path,
        json_path=json_path,
        md_path=md_path,
    )
    env_path.unlink()
    md_path.unlink()

    n = rerender(json_path, env_path, md_path)
    assert n == 1
    assert "GROQ_API_KEY=gsk_abc" in env_path.read_text()
    assert "Groq" in md_path.read_text()
