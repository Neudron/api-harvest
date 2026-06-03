"""CLI surface tests via typer's CliRunner. These check plumbing, not browser
behavior, so they run offline without a real Chrome.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from harvest.cli import app

runner = CliRunner()


def test_list_command_lists_32_providers() -> None:
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "32 providers" in result.stdout
    assert "google-gemini" in result.stdout
    assert "anthropic" in result.stdout


def test_status_command_empty() -> None:
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "state.json" in result.stdout


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "api-harvest" in result.stdout


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "api-harvest" in result.stdout


def test_doctor_runs() -> None:
    result = runner.invoke(app, ["doctor"])
    # Exit code may be 0 or 1 depending on env (e.g. missing Gemini key), but it
    # must always render the diagnostics table without crashing.
    assert result.exit_code in (0, 1)
    assert "doctor" in result.stdout
    assert "providers catalog parses" in result.stdout


def test_complete_slug_matches_prefix() -> None:
    from harvest.cli import _complete_slug

    assert "groq" in _complete_slug("gr")
    assert _complete_slug("zzz-no-such") == []


def test_report_command(tmp_path: Path, monkeypatch) -> None:
    from harvest import config

    outputs = tmp_path / "outputs"
    outputs.mkdir()
    (outputs / "keys.json").write_text(
        json.dumps(
            [
                {"provider_slug": "groq", "provider_name": "Groq", "tier": 1, "status": "done"},
                {"provider_slug": "x", "provider_name": "X", "tier": 1, "status": "failed",
                 "error": "boom"},
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "OUTPUTS_DIR", outputs)
    monkeypatch.setattr(config, "JSON_PATH", outputs / "keys.json")
    monkeypatch.setattr(config, "RUNTIME_DIR", tmp_path / ".harvest")
    result = runner.invoke(app, ["report"])
    assert result.exit_code == 0, result.stdout
    assert "2 providers" in result.stdout
    assert (outputs / "report.md").exists()
    assert "Success rate: **50%**" in (outputs / "report.md").read_text()


def test_ai_log_empty(tmp_path: Path, monkeypatch) -> None:
    from harvest import config

    monkeypatch.setattr(config, "AI_LOG_PATH", tmp_path / "ai_calls.jsonl")
    result = runner.invoke(app, ["ai-log"])
    assert result.exit_code == 0, result.stdout
    assert "No AI rescue calls" in result.stdout


def test_ai_log_summary(tmp_path: Path, monkeypatch) -> None:
    from harvest import config

    log = tmp_path / "ai_calls.jsonl"
    log.write_text(
        json.dumps({"provider": "groq", "suggestion": {"confidence": 0.9}}) + "\n"
        + json.dumps({"provider": "groq", "error": "boom"}) + "\n"
        + json.dumps({"provider": "cohere", "suggestion": {"confidence": 0.6}}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "AI_LOG_PATH", log)
    result = runner.invoke(app, ["ai-log"])
    assert result.exit_code == 0, result.stdout
    assert "3" in result.stdout  # total calls
    assert "groq" in result.stdout
    assert "cohere" in result.stdout


def test_run_dry_run_lists_plan(tmp_path: Path, monkeypatch) -> None:
    from harvest import config

    monkeypatch.setattr(config, "RUNTIME_DIR", tmp_path / ".harvest")
    monkeypatch.setattr(config, "STATE_PATH", tmp_path / ".harvest" / "state.json")
    monkeypatch.setattr(config, "OUTPUTS_DIR", tmp_path / "outputs")

    result = runner.invoke(app, ["run", "--dry-run", "--only", "groq"])
    assert result.exit_code == 0, result.stdout
    assert "dry run" in result.stdout.lower()
    assert "groq" in result.stdout
    assert "1 of" in result.stdout  # exactly one provider would run


def test_run_requires_browser_mode() -> None:
    """Neither --cdp-port nor --profile-dir should error with a tailored message."""
    result = runner.invoke(app, ["run"])
    assert result.exit_code == 2
    assert "browser mode" in result.stdout.lower()


def test_run_rejects_both_browser_modes() -> None:
    result = runner.invoke(app, ["run", "--cdp-port", "9222", "--profile-dir", "/tmp/foo"])
    assert result.exit_code == 2
    assert "mutually exclusive" in result.stdout.lower()


def test_export_rejects_unknown_format() -> None:
    result = runner.invoke(app, ["export", "--format", "bogus"])
    assert result.exit_code == 2
    assert "unknown --format" in result.stdout.lower()


def test_export_honors_md_only(tmp_path: Path, monkeypatch) -> None:
    """`harvest export --format md` should write keys.md but not .env."""
    # Point config paths at tmp_path
    from harvest import config

    monkeypatch.setattr(config, "OUTPUTS_DIR", tmp_path)
    monkeypatch.setattr(config, "ENV_PATH", tmp_path / ".env")
    monkeypatch.setattr(config, "JSON_PATH", tmp_path / "keys.json")
    monkeypatch.setattr(config, "MD_PATH", tmp_path / "keys.md")
    monkeypatch.setattr(config, "RUNTIME_DIR", tmp_path / ".harvest")
    monkeypatch.setattr(config, "STATE_PATH", tmp_path / ".harvest" / "state.json")

    # Seed a keys.json
    (tmp_path / "keys.json").write_text(
        json.dumps([
            {
                "provider_slug": "groq",
                "provider_name": "Groq",
                "tier": 1,
                "status": "done",
                "api_key": "gsk_abc",
                "env_var": "GROQ_API_KEY",
                "created_at": "2026-05-28T00:00:00",
                "dashboard_url": "",
                "rate_limits": "30 RPM",
            }
        ])
    )

    result = runner.invoke(app, ["export", "--format", "md"])
    assert result.exit_code == 0, result.stdout
    assert (tmp_path / "keys.md").exists()
    assert not (tmp_path / ".env").exists()  # md only, so env was not requested
