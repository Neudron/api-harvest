"""No-op AI backend for when AI assistance is disabled."""

from __future__ import annotations

from harvest.ai.base import LLMBackend, SelectorSuggestion


class NullBackend(LLMBackend):
    """AI backend that does nothing (AI rescue disabled)."""

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
        """Return a low-confidence empty suggestion."""
        return SelectorSuggestion(
            playwright_selector="",
            reason="AI assistance disabled",
            confidence=0.0,
        )
