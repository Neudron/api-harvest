from __future__ import annotations

import json
import os
from pathlib import Path

from harvest.models import HarvestResult, ProviderSpec, RunState
from harvest.output import secure_chmod


class StateStore:
    def __init__(self, path: Path):
        self.path = path
        self._state: RunState | None = None

    def load(self) -> RunState:
        if not self.path.exists():
            self._state = RunState()
            return self._state
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self._state = RunState.from_dict(data)
        return self._state

    @property
    def state(self) -> RunState:
        if self._state is None:
            return self.load()
        return self._state

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self.state.to_dict(), indent=2), encoding="utf-8")
        secure_chmod(tmp)
        os.replace(tmp, self.path)

    def mark(self, result: HarvestResult) -> None:
        self.state.results[result.provider_slug] = result
        self.save()

    def reset(self, slug: str | None) -> int:
        if slug is None:
            count = len(self.state.results)
            self.state.results.clear()
            self.save()
            return count
        if slug in self.state.results:
            del self.state.results[slug]
            self.save()
            return 1
        return 0


def plan_run(
    specs: list[ProviderSpec],
    state: RunState,
    only: set[str] | None = None,
    skip: set[str] | None = None,
) -> list[tuple[ProviderSpec, str]]:
    """Resolve which specs would run, and why each is included or excluded.

    Returns ``[(spec, disposition)]`` in run order, where ``disposition`` is
    ``"run"`` or a short reason it would be skipped. This is the single source
    of truth for ``--only``/``--skip``/resume filtering, shared by the
    ``run --dry-run`` preview and (later) the orchestrator itself.
    """
    plan: list[tuple[ProviderSpec, str]] = []
    for spec in specs:
        if only and spec.slug not in only:
            plan.append((spec, "excluded (--only)"))
            continue
        if skip and spec.slug in skip:
            plan.append((spec, "excluded (--skip)"))
            continue
        prev = state.results.get(spec.slug)
        if prev and prev.status == "done":
            plan.append((spec, "skip (already done)"))
            continue
        if prev and prev.user_skipped:
            plan.append((spec, "skip (user-skipped)"))
            continue
        plan.append((spec, "run"))
    return plan


def resume_filter(specs: list[ProviderSpec], state: RunState) -> tuple[list[ProviderSpec], list[ProviderSpec]]:
    """Split specs into (to_run, already_handled). Already-handled = done or user_skipped."""
    to_run: list[ProviderSpec] = []
    handled: list[ProviderSpec] = []
    for spec in specs:
        prev = state.results.get(spec.slug)
        if prev and (prev.status == "done" or prev.user_skipped):
            handled.append(spec)
        else:
            to_run.append(spec)
    return to_run, handled
