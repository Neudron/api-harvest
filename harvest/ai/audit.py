"""Pure aggregation of the AI audit log (``ai_calls.jsonl``).

``summarize()`` is a pure function over already-parsed records so it can be
unit-tested offline; ``load_records()`` handles the file I/O and tolerates
malformed lines.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AIAuditSummary:
    total_calls: int = 0
    errors: int = 0
    per_provider: dict[str, int] = field(default_factory=dict)
    # Providers where at least one suggestion had confidence >= threshold.
    confident_providers: set[str] = field(default_factory=set)

    @property
    def successes(self) -> int:
        return self.total_calls - self.errors

    @property
    def error_rate(self) -> float:
        return (self.errors / self.total_calls) if self.total_calls else 0.0


def load_records(path: Path) -> list[dict]:
    """Read ``ai_calls.jsonl``, skipping blank/corrupt lines. Never raises."""
    if not path.exists():
        return []
    records: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            records.append(obj)
    return records


def summarize(records: list[dict], *, confidence_threshold: float = 0.5) -> AIAuditSummary:
    """Aggregate audit records into counts per provider and rescue confidence.

    A record is counted as an error if it carries an ``error`` key (the call
    failed); otherwise it's a successful suggestion. ``confident_providers``
    collects providers that produced at least one suggestion meeting the
    confidence threshold.
    """
    summary = AIAuditSummary()
    for rec in records:
        summary.total_calls += 1
        provider = str(rec.get("provider", "unknown"))
        summary.per_provider[provider] = summary.per_provider.get(provider, 0) + 1

        if "error" in rec:
            summary.errors += 1
            continue

        suggestion = rec.get("suggestion")
        if isinstance(suggestion, dict):
            try:
                conf = float(suggestion.get("confidence", 0.0))
            except (TypeError, ValueError):
                conf = 0.0
            if conf >= confidence_threshold:
                summary.confident_providers.add(provider)
    return summary
