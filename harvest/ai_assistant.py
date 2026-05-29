from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field


class AIBudgetExhausted(Exception):
    pass


class SelectorSuggestion(BaseModel):
    playwright_selector: str = Field(..., description="A Playwright-compatible selector")
    reason: str = Field(default="", description="Brief explanation of why this selector should work")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


@dataclass
class _StepBudget:
    used: int = 0
    limit: int = 2


class AIAssistant:
    """Wraps google-genai for selector rescue. Strict budget + audit log."""

    def __init__(
        self,
        api_key: str,
        log_path: Path,
        model: str = "gemini-2.5-flash",
        per_run_budget: int = 30,
        per_step_budget: int = 2,
    ):
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._per_run_budget = per_run_budget
        self._per_step_budget = per_step_budget
        self._run_used = 0
        self._step_budgets: dict[str, _StepBudget] = {}
        self._log_path = log_path
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

    def _step_budget(self, step_id: str) -> _StepBudget:
        if step_id not in self._step_budgets:
            self._step_budgets[step_id] = _StepBudget(limit=self._per_step_budget)
        return self._step_budgets[step_id]

    def _check_budget(self, step_id: str) -> None:
        if self._run_used >= self._per_run_budget:
            raise AIBudgetExhausted(f"per-run AI budget {self._per_run_budget} exhausted")
        step = self._step_budget(step_id)
        if step.used >= step.limit:
            raise AIBudgetExhausted(f"per-step AI budget {step.limit} exhausted for {step_id}")

    def _log(self, payload: dict) -> None:
        from harvest.output import secure_chmod

        payload["ts"] = datetime.now(UTC).isoformat()
        with self._log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
        # The audit log records prompts/suggestions but not keys; still keep it
        # owner-only since it lives alongside the secrets in .harvest/.
        secure_chmod(self._log_path)

    async def rescue_selector(
        self,
        *,
        step_id: str,
        provider_name: str,
        goal: str,
        failed_selector: str,
        url: str,
        html_snippet: str,
        screenshot_png: bytes | None = None,
    ) -> SelectorSuggestion:
        from google.genai import types as genai_types

        self._check_budget(step_id)

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
            # Preferred: pass the Pydantic model class directly (google-genai
            # 2.x supports this via internal coercion).
            response = await _gen(SelectorSuggestion)
        except Exception:
            # Fall back to an explicit JSON Schema dict if the SDK in use
            # doesn't accept the BaseModel form.
            try:
                response = await _gen(SelectorSuggestion.model_json_schema())
            except Exception as e:
                self._log(
                    {
                        "step_id": step_id,
                        "provider": provider_name,
                        "goal": goal,
                        "failed_selector": failed_selector,
                        "error": str(e),
                    }
                )
                raise

        self._run_used += 1
        self._step_budget(step_id).used += 1

        text = response.text or "{}"
        try:
            parsed = SelectorSuggestion.model_validate_json(text)
        except Exception:
            data = json.loads(text) if text.strip() else {}
            parsed = SelectorSuggestion(
                playwright_selector=data.get("playwright_selector", ""),
                reason=data.get("reason", ""),
                confidence=float(data.get("confidence", 0.0)),
            )

        self._log(
            {
                "step_id": step_id,
                "provider": provider_name,
                "goal": goal,
                "failed_selector": failed_selector,
                "url": url,
                "suggestion": parsed.model_dump(),
                "run_used": self._run_used,
            }
        )
        return parsed

    @property
    def run_used(self) -> int:
        return self._run_used
