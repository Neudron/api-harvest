from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class ProviderSpec:
    slug: str
    name: str
    tier: Literal[1, 2]
    order_index: int
    signup_url: str
    api_key_url: str
    env_var: str | None
    requires_cc: bool
    requires_phone: bool
    rate_limits: str
    free_models: list[str]
    gotchas: str
    raw_section: str


StatusLiteral = Literal["pending", "running", "done", "failed", "skipped"]


@dataclass
class HarvestResult:
    provider_slug: str
    provider_name: str
    tier: int
    status: StatusLiteral
    api_key: str | None = None
    env_var: str | None = None
    created_at: str | None = None
    dashboard_url: str = ""
    rate_limits: str = ""
    error: str | None = None
    screenshot_path: str | None = None
    html_path: str | None = None
    user_skipped: bool = False
    notes: str | None = None

    def to_dict(self) -> dict:
        return {
            "provider_slug": self.provider_slug,
            "provider_name": self.provider_name,
            "tier": self.tier,
            "status": self.status,
            "api_key": self.api_key,
            "env_var": self.env_var,
            "created_at": self.created_at,
            "dashboard_url": self.dashboard_url,
            "rate_limits": self.rate_limits,
            "error": self.error,
            "screenshot_path": self.screenshot_path,
            "html_path": self.html_path,
            "user_skipped": self.user_skipped,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> HarvestResult:
        # Fall back to sensible defaults for required fields so older or partial
        # state.json entries don't crash the whole load.
        defaults = {
            "provider_slug": data.get("provider_slug") or "unknown",
            "provider_name": data.get("provider_name") or data.get("provider_slug") or "Unknown",
            "tier": data.get("tier") or 0,
            "status": data.get("status") or "failed",
        }
        kwargs = {}
        for k in cls.__dataclass_fields__:
            kwargs[k] = data.get(k, defaults.get(k))
        return cls(**kwargs)


@dataclass
class RunState:
    schema_version: int = 1
    started_at: str = field(default_factory=_iso_now)
    results: dict[str, HarvestResult] = field(default_factory=dict)
    ai_budget_used: int = 0

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "started_at": self.started_at,
            "ai_budget_used": self.ai_budget_used,
            "results": {k: v.to_dict() for k, v in self.results.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> RunState:
        results: dict[str, HarvestResult] = {}
        for k, v in data.get("results", {}).items():
            try:
                results[k] = HarvestResult.from_dict(v)
            except Exception:
                # Drop malformed entries instead of crashing the whole load.
                continue
        return cls(
            schema_version=data.get("schema_version", 1),
            started_at=data.get("started_at", _iso_now()),
            ai_budget_used=data.get("ai_budget_used", 0),
            results=results,
        )


class EventKind(StrEnum):
    START = "start"
    STEP = "step"
    LOG = "log"
    SUCCESS = "success"
    SKIP = "skip"
    FAIL = "fail"
    RETRY = "retry"
    AI_CALL = "ai_call"
    PROMPT = "prompt"
    DASHBOARD_PAUSE = "dashboard_pause"
    DASHBOARD_RESUME = "dashboard_resume"
    SKIP_REQUESTED = "skip_requested"
    QUIT_REQUESTED = "quit_requested"


@dataclass
class StepEvent:
    provider_slug: str
    kind: EventKind
    message: str = ""
    payload: dict = field(default_factory=dict)
    ts: str = field(default_factory=_iso_now)
