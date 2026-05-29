"""AI backend abstraction for selector rescue.

Provides a pluggable interface for different LLM providers (Gemini, OpenAI, Anthropic, etc).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    pass


class SelectorSuggestion(BaseModel):
    """AI-suggested Playwright selector with confidence score."""

    playwright_selector: str = Field(..., description="A Playwright-compatible selector")
    reason: str = Field(default="", description="Brief explanation of why this selector should work")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class LLMBackend(Protocol):
    """Protocol for LLM backends used in selector rescue."""

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
        """Suggest a Playwright selector to find an element.

        Args:
            provider_name: Name of the provider being automated.
            goal: What we're trying to do (e.g., "Find the API key display").
            failed_selector: The selector that failed.
            url: Current page URL.
            html_snippet: Trimmed HTML around the target element.
            screenshot_png: Optional page screenshot PNG bytes.

        Returns:
            SelectorSuggestion with confidence score.

        Raises:
            Various exceptions on network/API errors (caller handles retries).
        """
        ...
