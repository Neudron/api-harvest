"""AI backend abstraction and implementations."""

from __future__ import annotations

from harvest.ai.base import LLMBackend, SelectorSuggestion
from harvest.ai.fake import FakeBackend
from harvest.ai.gemini import GeminiBackend
from harvest.ai.null import NullBackend

__all__ = [
    "LLMBackend",
    "SelectorSuggestion",
    "GeminiBackend",
    "NullBackend",
    "FakeBackend",
    "make_backend",
]


def make_backend(
    api_key: str | None = None,
    model: str = "gemini-2.5-flash",
    backend_type: str = "gemini",
) -> LLMBackend:
    """Create an AI backend instance.

    Args:
        api_key: API key for the backend (if needed).
        model: Model to use (for Gemini).
        backend_type: Backend type ("gemini", "null", "fake").

    Returns:
        An LLMBackend implementation.

    Raises:
        ValueError: If backend_type is unknown or required api_key is missing.
    """
    match backend_type:
        case "gemini":
            if not api_key:
                raise ValueError("Gemini backend requires api_key")
            return GeminiBackend(api_key=api_key, model=model)
        case "null":
            return NullBackend()
        case "fake":
            return FakeBackend()
        case _:
            raise ValueError(f"Unknown backend type: {backend_type}")
