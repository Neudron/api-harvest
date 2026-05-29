from __future__ import annotations

from harvest.doctor import EXPECTED_PROVIDER_COUNT, run_checks


def test_run_checks_returns_tuples() -> None:
    checks = run_checks()
    assert checks, "doctor should produce at least one check"
    for name, ok, detail in checks:
        assert isinstance(name, str)
        assert isinstance(ok, bool)
        assert isinstance(detail, str)


def test_providers_check_passes() -> None:
    checks = {name: (ok, detail) for name, ok, detail in run_checks()}
    ok, detail = checks["providers catalog parses"]
    assert ok, detail
    assert str(EXPECTED_PROVIDER_COUNT) in detail


def test_gemini_key_check_reflects_env() -> None:
    with_key = {name: ok for name, ok, _ in run_checks(env={"GEMINI_API_KEY": "x"})}
    without_key = {name: ok for name, ok, _ in run_checks(env={})}
    assert with_key["Gemini API key set"] is True
    assert without_key["Gemini API key set"] is False
