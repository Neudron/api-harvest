"""Backward-compatible config shim.

This module maintains the old `from harvest import config; config.PROVIDERS_MD` API
while delegating to the new Settings system. Import `harvest.settings` directly for
production code.
"""

from __future__ import annotations

from harvest.settings import get_settings


def __getattr__(name: str):
    """Lazy delegation to Settings for old-style config attribute access."""
    settings = get_settings()
    # Map old config names to new Settings field names
    mapping = {
        "REPO_ROOT": "runtime_dir",  # Closest approximation
        "PROVIDERS_MD": "providers_md",
        "RUNTIME_DIR": "runtime_dir",
        "SCREENSHOTS_DIR": "screenshots_dir",
        "HTML_DIR": "html_dir",
        "STATE_PATH": "state_path",
        "AI_LOG_PATH": "ai_log_path",
        "OUTPUTS_DIR": "outputs_dir",
        "ENV_PATH": "env_path",
        "JSON_PATH": "json_path",
        "MD_PATH": "md_path",
        "DEFAULT_AI_MODEL": "ai_model",
        "DEFAULT_AI_BUDGET_PER_RUN": "ai_budget_per_run",
        "DEFAULT_AI_BUDGET_PER_STEP": "ai_budget_per_step",
        "PLAYWRIGHT_TIMEOUT_MS": "playwright_timeout_ms",
    }
    if name in mapping:
        return getattr(settings, mapping[name])
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def ensure_dirs() -> None:
    """Create necessary directories. Legacy function for backward compatibility."""
    settings = get_settings()
    for d in (
        settings.runtime_dir,
        settings.screenshots_dir,
        settings.html_dir,
        settings.outputs_dir,
    ):
        d.mkdir(parents=True, exist_ok=True)
