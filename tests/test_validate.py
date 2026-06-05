"""Offline tests for live key validation. The network call goes through an
injected ``opener`` so nothing here touches the network.
"""

from __future__ import annotations

import json
import urllib.error
from pathlib import Path

import pytest
from typer.testing import CliRunner

from harvest.cli import app
from harvest.validate import (
    VALIDATION_SPECS,
    ValidationOutcome,
    validate_key,
    validate_key_async,
)

runner = CliRunner()


class _Resp:
    def __init__(self, status: int) -> None:
        self.status = status

    def getcode(self) -> int:  # pragma: no cover - fallback path
        return self.status


def _opener_returning(status: int):
    captured: dict = {}

    def _opener(req, timeout=None):
        captured["req"] = req
        captured["timeout"] = timeout
        return _Resp(status)

    _opener.captured = captured  # type: ignore[attr-defined]
    return _opener


def _opener_raising(exc: Exception):
    def _opener(req, timeout=None):
        raise exc

    return _opener


def test_unknown_slug_is_unsupported() -> None:
    out = validate_key("not-a-real-provider", "key-123")
    assert out.status == "unsupported"


def test_missing_key_is_error() -> None:
    out = validate_key("groq", None)
    assert out.status == "error"


def test_200_is_valid() -> None:
    out = validate_key("groq", "gsk_abc", opener=_opener_returning(200))
    assert out.status == "valid"
    assert out.http_status == 200
    assert out.latency_ms is not None


@pytest.mark.parametrize("code", [401, 403])
def test_401_403_is_invalid(code: int) -> None:
    err = urllib.error.HTTPError("u", code, "no", None, None)
    out = validate_key("groq", "gsk_bad", opener=_opener_raising(err))
    assert out.status == "invalid"
    assert out.http_status == code


def test_429_counts_as_valid() -> None:
    err = urllib.error.HTTPError("u", 429, "slow down", None, None)
    out = validate_key("groq", "gsk_x", opener=_opener_raising(err))
    assert out.status == "valid"


def test_network_error_is_error() -> None:
    out = validate_key("groq", "gsk_x", opener=_opener_raising(urllib.error.URLError("down")))
    assert out.status == "error"


def test_unexpected_code_is_error() -> None:
    out = validate_key("groq", "gsk_x", opener=_opener_returning(500))
    assert out.status == "error"
    assert out.http_status == 500


def test_bearer_auth_header() -> None:
    opener = _opener_returning(200)
    validate_key("groq", "gsk_secret", opener=opener)
    req = opener.captured["req"]  # type: ignore[attr-defined]
    assert req.get_header("Authorization") == "Bearer gsk_secret"
    assert req.get_method() == "GET"


def test_x_api_key_auth_header() -> None:
    opener = _opener_returning(200)
    validate_key("anthropic", "sk-ant-123", opener=opener)
    req = opener.captured["req"]  # type: ignore[attr-defined]
    # urllib title-cases header keys.
    assert req.get_header("X-api-key") == "sk-ant-123"
    assert req.get_header("Anthropic-version") == "2023-06-01"


def test_query_key_auth_appends_to_url() -> None:
    opener = _opener_returning(200)
    validate_key("google-gemini-ai-studio", "AIzaXYZ", opener=opener)
    req = opener.captured["req"]  # type: ignore[attr-defined]
    assert req.full_url.endswith("?key=AIzaXYZ")
    assert req.get_header("Authorization") is None


async def test_async_matches_sync() -> None:
    out = await validate_key_async("groq", "gsk_abc", opener=_opener_returning(200))
    assert out.status == "valid"


def test_every_spec_has_a_url() -> None:
    for slug, spec in VALIDATION_SPECS.items():
        assert spec.url.startswith("https://"), slug
        assert spec.auth in ("bearer", "x_api_key", "query_key"), slug


def _seed_keys(outputs: Path, rows: list[dict]) -> None:
    outputs.mkdir(parents=True, exist_ok=True)
    (outputs / "keys.json").write_text(json.dumps(rows), encoding="utf-8")


def test_validate_command_updates_keys_and_exit_code(tmp_path: Path, monkeypatch) -> None:
    from harvest import config
    from harvest import validate as validate_mod

    outputs = tmp_path / "outputs"
    _seed_keys(
        outputs,
        [
            {"provider_slug": "groq", "provider_name": "Groq", "tier": 1,
             "status": "done", "api_key": "gsk_good", "env_var": "GROQ_API_KEY"},
            {"provider_slug": "cohere", "provider_name": "Cohere", "tier": 1,
             "status": "done", "api_key": "co_bad", "env_var": "COHERE_API_KEY"},
        ],
    )
    monkeypatch.setattr(config, "OUTPUTS_DIR", outputs)
    monkeypatch.setattr(config, "JSON_PATH", outputs / "keys.json")
    monkeypatch.setattr(config, "MD_PATH", outputs / "keys.md")
    monkeypatch.setattr(config, "RUNTIME_DIR", tmp_path / ".harvest")

    # groq -> valid, cohere -> invalid
    def fake_validate(slug, key, **kwargs):
        if slug == "cohere":
            return ValidationOutcome(status="invalid", http_status=401, detail="rejected")
        return ValidationOutcome(status="valid", http_status=200, detail="ok", latency_ms=5)

    monkeypatch.setattr(validate_mod, "validate_key", fake_validate)

    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 1, result.stdout  # an invalid key -> non-zero
    assert "valid" in result.stdout
    assert "invalid" in result.stdout

    stored = json.loads((outputs / "keys.json").read_text())
    by_slug = {r["provider_slug"]: r for r in stored}
    assert by_slug["groq"]["validation_status"] == "valid"
    assert by_slug["cohere"]["validation_status"] == "invalid"
    assert "✓" in (outputs / "keys.md").read_text()


def test_validate_command_no_keys(tmp_path: Path, monkeypatch) -> None:
    from harvest import config

    outputs = tmp_path / "outputs"
    _seed_keys(outputs, [])
    monkeypatch.setattr(config, "OUTPUTS_DIR", outputs)
    monkeypatch.setattr(config, "JSON_PATH", outputs / "keys.json")
    monkeypatch.setattr(config, "MD_PATH", outputs / "keys.md")
    monkeypatch.setattr(config, "RUNTIME_DIR", tmp_path / ".harvest")

    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 0, result.stdout
    assert "No harvested keys" in result.stdout
