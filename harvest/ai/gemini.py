"""Google Gemini backend for AI selector rescue."""

from __future__ import annotations

from harvest.ai.base import LLMBackend, SelectorSuggestion


class GeminiBackend(LLMBackend):
    """Google Gemini-powered selector suggestion backend."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        """Initialize Gemini backend.

        Args:
            api_key: Google Gemini API key.
            model: Gemini model to use.
        """
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model = model

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
        """Use Gemini to suggest a selector."""
        from google.genai import types as genai_types

        prompt = (
            "You are a Playwright selector assistant. A Playwright selector failed.\n"
            "Return ONLY JSON matching this schema: "
            '{"playwright_selector": "<selector>", "reason": "<why>", "confidence": <0..1>}.\n'
            "Prefer text-based selectors when possible (e.g. role=button[name=...] or text=...).\n\n"
            f"Provider: {provider_name}\n"
            f"URL: {url}\n"
            f"Goal: {goal}\n"
            f"Failed selector: {failed_selector}\n\n"
            f"DOM snippet (trimmed):\n```html\n{html_snippet[:8000]}\n```\n"
        )

        contents: list = [prompt]
        if screenshot_png:
            contents.append(
                genai_types.Part.from_bytes(data=screenshot_png, mime_type="image/png")
            )

        async def _gen(schema):
            return await self._client.aio.models.generate_content(
                model=self._model,
                contents=contents,
                config=genai_types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )

        try:
            # Preferred: pass the Pydantic model class directly
            response = await _gen(SelectorSuggestion)
        except Exception:
            # Fall back to explicit JSON Schema dict if the SDK doesn't accept BaseModel
            try:
                response = await _gen(SelectorSuggestion.model_json_schema())
            except Exception:
                raise

        text = response.text or "{}"
        try:
            parsed = SelectorSuggestion.model_validate_json(text)
        except Exception:
            import json

            data = json.loads(text) if text.strip() else {}
            parsed = SelectorSuggestion(
                playwright_selector=data.get("playwright_selector", ""),
                reason=data.get("reason", ""),
                confidence=float(data.get("confidence", 0.0)),
            )

        return parsed
