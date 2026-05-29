"""AI-powered selector rescue with budget tracking and audit logging."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from harvest.ai.base import LLMBackend, SelectorSuggestion


class AIBudgetExhausted(Exception):
    """Raised when AI budget is exhausted."""

    pass


@dataclass
class _StepBudget:
    """Tracks AI calls per step."""

    used: int = 0
    limit: int = 2


class AIAssistant:
    """Wraps an LLMBackend with budget enforcement and audit logging."""

    def __init__(
        self,
        backend: LLMBackend,
        log_path: Path,
        per_run_budget: int = 30,
        per_step_budget: int = 2,
    ):
        """Initialize AIAssistant.

        Args:
            backend: LLMBackend implementation (Gemini, Anthropic, fake, null, etc).
            log_path: Path to audit log (JSONL).
            per_run_budget: Max AI calls per run.
            per_step_budget: Max AI calls per step.
        """
        self._backend = backend
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
        """Use backend to suggest a selector, enforcing budgets and logging."""
        self._check_budget(step_id)

        try:
            parsed = await self._backend.suggest_selector(
                provider_name=provider_name,
                goal=goal,
                failed_selector=failed_selector,
                url=url,
                html_snippet=html_snippet,
                screenshot_png=screenshot_png,
            )
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
