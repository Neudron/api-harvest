"""Tests for AI backend abstraction."""

from __future__ import annotations

import pytest

from harvest.ai import FakeBackend, NullBackend, SelectorSuggestion, make_backend
from harvest.ai_assistant import AIAssistant, AIBudgetExhausted


@pytest.mark.asyncio
async def test_fake_backend_returns_suggestion() -> None:
    """FakeBackend returns canned suggestions for testing."""
    backend = FakeBackend(default_selector="role=button[name=Get]", default_confidence=0.95)
    suggestion = await backend.suggest_selector(
        provider_name="test",
        goal="Click button",
        failed_selector="[data-id=get]",
        url="http://test.com",
        html_snippet="<button>Get</button>",
    )
    assert suggestion.playwright_selector == "role=button[name=Get]"
    assert suggestion.confidence == 0.95
    assert backend.call_count == 1


@pytest.mark.asyncio
async def test_fake_backend_tracks_calls() -> None:
    """FakeBackend records call arguments for verification."""
    backend = FakeBackend()
    await backend.suggest_selector(
        provider_name="groq",
        goal="Find API key",
        failed_selector="[data-key]",
        url="http://groq.test",
        html_snippet="<div>key_abc123</div>",
        screenshot_png=b"fake-png",
    )
    assert backend.call_count == 1
    assert backend.last_call_args["provider_name"] == "groq"
    assert backend.last_call_args["goal"] == "Find API key"
    assert backend.last_call_args["screenshot_png"] is True


@pytest.mark.asyncio
async def test_fake_backend_fail_on_call() -> None:
    """FakeBackend can be configured to fail (for testing error handling)."""
    backend = FakeBackend(fail_on_call=True)
    with pytest.raises(RuntimeError, match="configured to fail"):
        await backend.suggest_selector(
            provider_name="test",
            goal="test",
            failed_selector="test",
            url="test",
            html_snippet="test",
        )


@pytest.mark.asyncio
async def test_null_backend_always_fails() -> None:
    """NullBackend returns low-confidence empty suggestion (disabled)."""
    backend = NullBackend()
    suggestion = await backend.suggest_selector(
        provider_name="test",
        goal="test",
        failed_selector="test",
        url="test",
        html_snippet="test",
    )
    assert suggestion.playwright_selector == ""
    assert suggestion.confidence == 0.0
    assert "disabled" in suggestion.reason


@pytest.mark.asyncio
async def test_ai_assistant_with_fake_backend(tmp_path) -> None:
    """AIAssistant works with any LLMBackend (testing with FakeBackend)."""
    backend = FakeBackend(default_selector="[data-api-key]")
    log_path = tmp_path / "ai.jsonl"
    assistant = AIAssistant(backend=backend, log_path=log_path)

    suggestion = await assistant.rescue_selector(
        step_id="step_1",
        provider_name="test",
        goal="find key",
        failed_selector="[key]",
        url="http://test",
        html_snippet="<input value=key>",
    )

    assert suggestion.playwright_selector == "[data-api-key]"
    assert assistant.run_used == 1
    assert log_path.exists()
    # Verify log contains the suggestion
    log_content = log_path.read_text()
    assert "find key" in log_content
    assert "[data-api-key]" in log_content


@pytest.mark.asyncio
async def test_ai_assistant_enforces_per_run_budget(tmp_path) -> None:
    """AIAssistant stops making calls after per-run budget is exhausted."""
    backend = FakeBackend()
    assistant = AIAssistant(backend=backend, log_path=tmp_path / "ai.jsonl", per_run_budget=2)

    # First two calls succeed
    await assistant.rescue_selector(
        step_id="a", provider_name="p", goal="g", failed_selector="s", url="u", html_snippet="h"
    )
    await assistant.rescue_selector(
        step_id="b", provider_name="p", goal="g", failed_selector="s", url="u", html_snippet="h"
    )

    # Third call hits budget limit
    with pytest.raises(AIBudgetExhausted, match="per-run"):
        await assistant.rescue_selector(
            step_id="c", provider_name="p", goal="g", failed_selector="s", url="u", html_snippet="h"
        )

    assert assistant.run_used == 2


@pytest.mark.asyncio
async def test_ai_assistant_enforces_per_step_budget(tmp_path) -> None:
    """AIAssistant stops making calls for same step after per-step budget is exhausted."""
    backend = FakeBackend()
    assistant = AIAssistant(
        backend=backend, log_path=tmp_path / "ai.jsonl", per_run_budget=10, per_step_budget=1
    )

    # First call for step_1 succeeds
    await assistant.rescue_selector(
        step_id="step_1", provider_name="p", goal="g", failed_selector="s", url="u", html_snippet="h"
    )

    # Second call for same step hits per-step budget
    with pytest.raises(AIBudgetExhausted, match="per-step"):
        await assistant.rescue_selector(
            step_id="step_1", provider_name="p", goal="g", failed_selector="s", url="u", html_snippet="h"
        )

    # But different step should work
    await assistant.rescue_selector(
        step_id="step_2", provider_name="p", goal="g", failed_selector="s", url="u", html_snippet="h"
    )

    assert assistant.run_used == 2


@pytest.mark.asyncio
async def test_ai_assistant_logs_errors(tmp_path) -> None:
    """AIAssistant logs errors to audit log."""
    backend = FakeBackend(fail_on_call=True)
    log_path = tmp_path / "ai.jsonl"
    assistant = AIAssistant(backend=backend, log_path=log_path)

    with pytest.raises(RuntimeError):
        await assistant.rescue_selector(
            step_id="s", provider_name="p", goal="g", failed_selector="f", url="u", html_snippet="h"
        )

    log_content = log_path.read_text()
    assert "error" in log_content


def test_make_backend_gemini_requires_key() -> None:
    """make_backend raises if Gemini selected but no key provided."""
    with pytest.raises(ValueError, match="Gemini.*api_key"):
        make_backend(backend_type="gemini")


@pytest.mark.skip(reason="GeminiBackend requires google-genai which has env issues in tests")
def test_make_backend_gemini_success() -> None:
    """make_backend returns GeminiBackend class when key is provided."""
    backend = make_backend(api_key="test-key", backend_type="gemini")
    assert backend.__class__.__name__ == "GeminiBackend"


def test_make_backend_null() -> None:
    """make_backend creates NullBackend."""
    backend = make_backend(backend_type="null")
    assert isinstance(backend, NullBackend)


def test_make_backend_fake() -> None:
    """make_backend creates FakeBackend."""
    backend = make_backend(backend_type="fake")
    assert isinstance(backend, FakeBackend)


def test_make_backend_unknown() -> None:
    """make_backend raises on unknown backend type."""
    with pytest.raises(ValueError, match="Unknown"):
        make_backend(backend_type="unknown")


def test_selector_suggestion_model() -> None:
    """SelectorSuggestion is a valid Pydantic model."""
    sugg = SelectorSuggestion(
        playwright_selector="[id=test]",
        reason="Test",
        confidence=0.8,
    )
    assert sugg.playwright_selector == "[id=test]"
    assert sugg.confidence == 0.8

    # Test serialization
    data = sugg.model_dump()
    assert data["playwright_selector"] == "[id=test]"
    assert data["confidence"] == 0.8

    # Test deserialization
    sugg2 = SelectorSuggestion.model_validate_json(sugg.model_dump_json())
    assert sugg2.playwright_selector == "[id=test]"
