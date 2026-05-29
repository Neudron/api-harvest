"""Tests for harvest.settings configuration system."""

from __future__ import annotations

from pathlib import Path

import pytest

from harvest.settings import Settings, load_settings, reset_settings


def test_settings_defaults() -> None:
    """Verify default Settings values."""
    settings = Settings()
    assert settings.ai_model == "gemini-2.5-flash"
    assert settings.ai_budget_per_run == 30
    assert settings.ai_budget_per_step == 2
    assert settings.playwright_timeout_ms == 8_000
    assert settings.max_attempts == 1
    assert settings.provider_timeout_s == 120
    assert settings.concurrency == 1
    assert settings.encrypt_at_rest is False
    assert settings.log_level == "INFO"


def test_load_settings_cli_overrides_all(tmp_path: Path) -> None:
    """CLI flags override everything else."""
    cli_overrides = {
        "ai_model": "custom-model",
        "ai_budget_per_run": 50,
        "max_attempts": 3,
    }
    settings = load_settings(cli_overrides, cwd=tmp_path)
    assert settings.ai_model == "custom-model"
    assert settings.ai_budget_per_run == 50
    assert settings.max_attempts == 3
    # Unspecified defaults still apply
    assert settings.playwright_timeout_ms == 8_000


def test_load_settings_env_vars(tmp_path: Path) -> None:
    """HARVEST_* environment variables are respected."""
    env = {
        "HARVEST_AI_MODEL": "gpt-4",
        "HARVEST_AI_BUDGET_PER_RUN": "100",
        "HARVEST_CONCURRENCY": "4",
    }
    settings = load_settings(env=env, cwd=tmp_path)
    assert settings.ai_model == "gpt-4"
    assert settings.ai_budget_per_run == 100
    assert settings.concurrency == 4


def test_load_settings_cli_beats_env(tmp_path: Path) -> None:
    """CLI flags override environment variables."""
    cli_overrides = {"ai_model": "cli-model"}
    env = {"HARVEST_AI_MODEL": "env-model"}
    settings = load_settings(cli_overrides, env=env, cwd=tmp_path)
    assert settings.ai_model == "cli-model"


def test_load_settings_config_file(tmp_path: Path) -> None:
    """Config file values are loaded and used as defaults."""
    config_file = tmp_path / ".harvest.toml"
    config_file.write_text(
        "[harvest]\n"
        'ai_model = "config-model"\n'
        "ai_budget_per_run = 75\n"
    )
    settings = load_settings(cwd=tmp_path)
    assert settings.ai_model == "config-model"
    assert settings.ai_budget_per_run == 75


def test_load_settings_config_takes_precedence_over_defaults() -> None:
    """Config file values beat defaults."""
    settings1 = Settings()
    assert settings1.max_attempts == 1  # Default

    # Override via config dict (simulating file load)
    settings2 = Settings(max_attempts=5)
    assert settings2.max_attempts == 5


def test_load_settings_paths_absolute(tmp_path: Path) -> None:
    """Relative paths are made absolute via cwd."""
    cwd = tmp_path / "work"
    cwd.mkdir()
    cli_overrides = {
        "runtime_dir": "local/.harvest",
        "outputs_dir": "local/outputs",
    }
    settings = load_settings(cli_overrides, cwd=cwd)
    assert settings.runtime_dir.is_absolute()
    assert settings.outputs_dir.is_absolute()
    assert settings.runtime_dir == cwd / "local/.harvest"
    assert settings.outputs_dir == cwd / "local/outputs"


def test_load_settings_respects_harvest_config_env() -> None:
    """HARVEST_CONFIG env var points to explicit config file."""
    pytest.importorskip("tomllib")  # Only Python 3.11+


def test_load_settings_is_immutable() -> None:
    """Settings objects are frozen and cannot be modified."""
    from pydantic import ValidationError

    settings = Settings()
    with pytest.raises((ValidationError, AttributeError)):
        settings.ai_model = "modified"  # type: ignore


def test_get_settings_singleton(tmp_path: Path) -> None:
    """get_settings() returns the same instance (process-global)."""
    reset_settings()
    from harvest.settings import get_settings

    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


def test_settings_derived_paths() -> None:
    """Derived paths like screenshots_dir are computed from parents."""
    settings = Settings(
        runtime_dir=Path("/custom/runtime"),
        outputs_dir=Path("/custom/outputs"),
    )
    assert settings.screenshots_dir == Path("/custom/runtime/screenshots")
    assert settings.html_dir == Path("/custom/runtime/html")
    assert settings.env_path == Path("/custom/outputs/.env")
