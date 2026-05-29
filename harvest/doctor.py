"""Preflight diagnostics for api-harvest.

`run_checks()` is a pure, read-only, exception-safe function returning a list of
``(name, ok, detail)`` tuples so it can be unit-tested offline without launching
a browser or hitting the network. The CLI `doctor` command just renders them.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

from harvest import config
from harvest.parser import build_run_order, parse_providers_md

EXPECTED_PROVIDER_COUNT = 32

Check = tuple[str, bool, str]


def _nearest_existing(path: Path) -> Path:
    """Walk up until we find a directory that exists (for writability checks)."""
    p = path
    while not p.exists() and p != p.parent:
        p = p.parent
    return p


def _check_providers() -> Check:
    try:
        specs = build_run_order(parse_providers_md(config.PROVIDERS_MD))
    except Exception as e:  # pragma: no cover - defensive
        return ("providers catalog parses", False, f"{type(e).__name__}: {e}")
    ok = len(specs) == EXPECTED_PROVIDER_COUNT
    return (
        "providers catalog parses",
        ok,
        f"{len(specs)} providers parsed (expected {EXPECTED_PROVIDER_COUNT})",
    )


def _check_outputs_writable() -> Check:
    target = _nearest_existing(config.OUTPUTS_DIR)
    ok = os.access(target, os.W_OK)
    return ("outputs directory writable", ok, str(config.OUTPUTS_DIR))


def _check_gemini_key(env: dict[str, str] | None = None) -> Check:
    env = os.environ if env is None else env
    name = next(
        (k for k in ("GEMINI_API_KEY", "GOOGLE_GENERATIVE_AI_API_KEY") if env.get(k)),
        None,
    )
    if name:
        return ("Gemini API key set", True, f"found {name}")
    return (
        "Gemini API key set",
        False,
        "no GEMINI_API_KEY/GOOGLE_GENERATIVE_AI_API_KEY (AI selector rescue disabled)",
    )


def _check_importable(label: str, module: str) -> Check:
    try:
        found = importlib.util.find_spec(module) is not None
    except (ImportError, ValueError):
        found = False
    return (label, found, module if found else f"{module} not importable")


def run_checks(env: dict[str, str] | None = None) -> list[Check]:
    """Return diagnostic checks. Read-only and never raises."""
    return [
        _check_providers(),
        _check_outputs_writable(),
        _check_gemini_key(env),
        _check_importable("Playwright installed", "playwright"),
        _check_importable("google-genai installed", "google.genai"),
    ]
