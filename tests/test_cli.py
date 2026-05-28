"""CLI surface tests via typer's CliRunner. Validates plumbing — not browser
behavior — so these run offline without a real Chrome.
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
    assert not (tmp_path / ".env").exists()  # md only — env was not requested
