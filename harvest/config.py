from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROVIDERS_MD = REPO_ROOT / "providers.md"
RUNTIME_DIR = REPO_ROOT / ".harvest"
SCREENSHOTS_DIR = RUNTIME_DIR / "screenshots"
HTML_DIR = RUNTIME_DIR / "html"
STATE_PATH = RUNTIME_DIR / "state.json"
AI_LOG_PATH = RUNTIME_DIR / "ai_calls.jsonl"

OUTPUTS_DIR = REPO_ROOT / "outputs"
ENV_PATH = OUTPUTS_DIR / ".env"
JSON_PATH = OUTPUTS_DIR / "keys.json"
MD_PATH = OUTPUTS_DIR / "keys.md"

DEFAULT_AI_MODEL = "gemini-2.5-flash"
DEFAULT_AI_BUDGET_PER_RUN = 30
DEFAULT_AI_BUDGET_PER_STEP = 2
PLAYWRIGHT_TIMEOUT_MS = 8_000


def ensure_dirs() -> None:
    for d in (RUNTIME_DIR, SCREENSHOTS_DIR, HTML_DIR, OUTPUTS_DIR):
        d.mkdir(parents=True, exist_ok=True)
