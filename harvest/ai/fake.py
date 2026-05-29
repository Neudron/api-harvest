"""Fake AI backend for testing (no network, no google-genai required)."""

from __future__ import annotations

from harvest.ai.base import LLMBackend, SelectorSuggestion


class FakeBackend(LLMBackend):
    """Test-only AI backend that returns canned responses."""

    def __init__(
        self,
        default_selector: str = "test-selector",
        default_confidence: float = 0.9,
        fail_on_call: bool = False,
    ):
        """Initialize fake backend.

        Args:
            default_selector: Selector to return on suggest_selector call.
            default_confidence: Confidence score for the suggestion.
            fail_on_call: If True, raise an exception on suggest_selector (to test error handling).
        """
        self.default_selector = default_selector
        self.default_confidence = default_confidence
        self.fail_on_call = fail_on_call
        self.call_count = 0
        self.last_call_args: dict | None = None

    async def suggest_selector(
        self,
        *,
        provider_name: str,
        goal: str,
        failed_selector: str,
        url: str,
        html_snippet: str,
        screenshot_png: bytes | None = None,
    ) -> SelectorSuggestion:
        """Return a canned response (for testing)."""
        self.call_count += 1
        self.last_call_args = {
            "provider_name": provider_name,
            "goal": goal,
            "failed_selector": failed_selector,
            "url": url,
            "html_snippet": html_snippet,
            "screenshot_png": screenshot_png is not None,
        }

        if self.fail_on_call:
            raise RuntimeError("FakeBackend configured to fail")

        return SelectorSuggestion(
            playwright_selector=self.default_selector,
            reason=f"Test suggestion for {provider_name}",
            confidence=self.default_confidence,
        )
