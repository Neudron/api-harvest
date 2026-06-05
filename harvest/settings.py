"""Configuration system for api-harvest.

Settings are resolved in order of precedence:
1. CLI flags (passed as cli_overrides dict)
2. Environment variables (HARVEST_* prefix)
3. Config file (~/.config/api-harvest/config.toml, then ./.harvest.toml)
4. Defaults
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, computed_field


class Settings(BaseModel):
    """Immutable configuration container."""

    model_config = ConfigDict(frozen=True)

    # Paths: all resolved to absolute paths at load time
    providers_md: Path = Field(
        default=Path.cwd() / "providers.md",
        description="Path to providers.md catalog",
    )
    runtime_dir: Path = Field(
        default=Path.cwd() / ".harvest",
        description="Directory for runtime state (screenshots, html, state.json, ai_calls.jsonl)",
    )
    outputs_dir: Path = Field(
        default=Path.cwd() / "outputs",
        description="Directory for output files (.env, keys.json, keys.md)",
    )

    # Derived paths (computed from runtime_dir and outputs_dir, so no field declaration)
    # See @computed_field methods below

    # AI settings
    ai_model: str = Field(
        default="gemini-2.5-flash",
        description="AI model to use for selector rescue",
    )
    ai_budget_per_run: int = Field(
        default=30,
        ge=1,
        description="Max AI calls per run",
    )
    ai_budget_per_step: int = Field(
        default=2,
        ge=1,
        description="Max AI calls per handler step",
    )

    # Playwright settings
    playwright_timeout_ms: int = Field(
        default=8_000,
        ge=100,
        description="Playwright timeout in milliseconds",
    )

    # Resilience
    max_attempts: int = Field(
        default=1,
        ge=1,
        description="Max attempts per provider (retries disabled by default)",
    )
    provider_timeout_s: int = Field(
        default=120,
        ge=1,
        description="Wall-clock timeout per provider in seconds",
    )
    validate_keys: bool = Field(
        default=False,
        description="Probe each captured key against its provider API (run --validate)",
    )

    # Parallelism (architectural, default OFF)
    concurrency: int = Field(
        default=1,
        ge=1,
        description="Max concurrent provider handlers (1 = serial)",
    )

    # Encryption (architectural, default OFF)
    encrypt_at_rest: bool = Field(
        default=False,
        description="Encrypt keys.json at rest (requires HARVEST_PASSPHRASE env or prompt)",
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Log level (DEBUG, INFO, WARNING, ERROR)",
    )

    @computed_field
    @property
    def screenshots_dir(self) -> Path:
        """Screenshots directory (computed from runtime_dir)."""
        return self.runtime_dir / "screenshots"

    @computed_field
    @property
    def html_dir(self) -> Path:
        """HTML capture directory (computed from runtime_dir)."""
        return self.runtime_dir / "html"

    @computed_field
    @property
    def state_path(self) -> Path:
        """Path to state.json (computed from runtime_dir)."""
        return self.runtime_dir / "state.json"

    @computed_field
    @property
    def ai_log_path(self) -> Path:
        """Path to AI audit log (computed from runtime_dir)."""
        return self.runtime_dir / "ai_calls.jsonl"

    @computed_field
    @property
    def env_path(self) -> Path:
        """Path to .env output file (computed from outputs_dir)."""
        return self.outputs_dir / ".env"

    @computed_field
    @property
    def json_path(self) -> Path:
        """Path to keys.json output file (computed from outputs_dir)."""
        return self.outputs_dir / "keys.json"

    @computed_field
    @property
    def md_path(self) -> Path:
        """Path to keys.md output file (computed from outputs_dir)."""
        return self.outputs_dir / "keys.md"


def load_settings(
    cli_overrides: dict[str, object] | None = None,
    *,
    cwd: Path | None = None,
    home: Path | None = None,
    env: dict[str, str] | None = None,
) -> Settings:
    """Load settings from all sources in order of precedence.

    Args:
        cli_overrides: CLI flags as dict (highest precedence)
        cwd: Working directory for relative path resolution (default: Path.cwd())
        home: Home directory for config file search (default: Path.home())
        env: Environment dict to use (default: os.environ)

    Returns:
        Resolved Settings object with all paths absolute.
    """
    cli_overrides = cli_overrides or {}
    cwd = cwd or Path.cwd()
    home = home or Path.home()
    env = env or os.environ

    # Start with defaults (Pydantic model defaults)
    merged: dict[str, object] = {}

    # Layer 2: Environment (HARVEST_* prefix, snake_case field names)
    for key, value in env.items():
        if key.startswith("HARVEST_"):
            field_name = key[8:].lower()  # Strip HARVEST_ prefix
            merged[field_name] = value

    # Layer 3: Config file
    config_file: Path | None = None
    if env.get("HARVEST_CONFIG"):
        config_file = Path(env["HARVEST_CONFIG"])
    else:
        # Try ~/.config/api-harvest/config.toml, then ./.harvest.toml
        candidates = [
            home / ".config" / "api-harvest" / "config.toml",
            cwd / ".harvest.toml",
        ]
        for candidate in candidates:
            if candidate.exists():
                config_file = candidate
                break

    if config_file and config_file.exists():
        try:
            with open(config_file, "rb") as f:
                file_config = tomllib.load(f)
                # Top-level keys or [harvest] section
                if "harvest" in file_config:
                    file_config = file_config["harvest"]
                merged.update(file_config)
        except Exception:
            pass  # Gracefully ignore config file errors

    # Layer 1: CLI overrides (highest precedence, filter out None values)
    for key, value in cli_overrides.items():
        if value is not None:
            merged[key] = value

    # Normalize base path strings to Path objects (only the non-derived paths)
    base_path_fields = {"providers_md", "runtime_dir", "outputs_dir"}
    for field in base_path_fields:
        if field in merged and isinstance(merged[field], str):
            p = Path(merged[field])
            merged[field] = p if p.is_absolute() else cwd / p

    # Construct Settings (derived paths are computed automatically)
    settings = Settings(**merged)

    # Convert base paths to absolute; derived paths will follow automatically
    settings = Settings(
        providers_md=settings.providers_md.resolve(),
        runtime_dir=settings.runtime_dir.resolve(),
        outputs_dir=settings.outputs_dir.resolve(),
        ai_model=settings.ai_model,
        ai_budget_per_run=settings.ai_budget_per_run,
        ai_budget_per_step=settings.ai_budget_per_step,
        playwright_timeout_ms=settings.playwright_timeout_ms,
        max_attempts=settings.max_attempts,
        provider_timeout_s=settings.provider_timeout_s,
        validate_keys=settings.validate_keys,
        concurrency=settings.concurrency,
        encrypt_at_rest=settings.encrypt_at_rest,
        log_level=settings.log_level,
    )

    return settings


# Process-global Settings instance (initialized on first access via config.py shim)
_SETTINGS: Settings | None = None


def get_settings() -> Settings:
    """Get or initialize the process-global Settings."""
    global _SETTINGS
    if _SETTINGS is None:
        _SETTINGS = load_settings()
    return _SETTINGS


def reset_settings() -> None:
    """Reset process-global Settings (for testing)."""
    global _SETTINGS
    _SETTINGS = None
