"""Run summary report rendering.

``render_report()`` is a pure function over a list of result dicts (the same
shape as ``keys.json`` entries / ``HarvestResult.to_dict()``), so it is fully
offline-testable. ``build_report()`` wires in the file I/O.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


def _summarize_counts(results: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for r in results:
        counts[str(r.get("status", "unknown"))] += 1
    return dict(counts)


def render_report(results: list[dict]) -> str:
    """Render a Markdown run summary from result dicts.

    Sections: overall counts + success rate, per-tier breakdown, and a list of
    failure reasons for any failed providers.
    """
    total = len(results)
    counts = _summarize_counts(results)
    done = counts.get("done", 0)
    success_rate = (done / total * 100.0) if total else 0.0

    lines: list[str] = ["# Run Summary", ""]
    lines.append(f"- Total providers: **{total}**")
    lines.append(f"- Succeeded: **{done}**")
    lines.append(f"- Failed: **{counts.get('failed', 0)}**")
    lines.append(f"- Skipped: **{counts.get('skipped', 0)}**")
    lines.append(f"- Success rate: **{success_rate:.0f}%**")
    lines.append("")

    # Per-tier breakdown
    by_tier: dict[int, list[dict]] = defaultdict(list)
    for r in results:
        by_tier[int(r.get("tier", 0))].append(r)

    if by_tier:
        lines.append("## Per-tier")
        lines.append("")
        lines.append("| Tier | Total | Done | Failed | Skipped | Success rate |")
        lines.append("|---|---|---|---|---|---|")
        for tier in sorted(by_tier):
            group = by_tier[tier]
            g_counts = _summarize_counts(group)
            g_done = g_counts.get("done", 0)
            g_rate = (g_done / len(group) * 100.0) if group else 0.0
            lines.append(
                f"| {tier} | {len(group)} | {g_done} | "
                f"{g_counts.get('failed', 0)} | {g_counts.get('skipped', 0)} | {g_rate:.0f}% |"
            )
        lines.append("")

    # Failure reasons
    failures = [r for r in results if r.get("status") == "failed"]
    if failures:
        lines.append("## Failures")
        lines.append("")
        for r in sorted(failures, key=lambda x: str(x.get("provider_slug", ""))):
            name = r.get("provider_name") or r.get("provider_slug") or "unknown"
            reason = (r.get("error") or r.get("notes") or "no reason recorded").strip()
            # Keep each reason to a single line.
            reason = reason.splitlines()[0] if reason else "no reason recorded"
            lines.append(f"- **{name}**: {reason[:200]}")
        lines.append("")

    return "\n".join(lines)


def build_report(json_path: Path, report_path: Path) -> int:
    """Read ``keys.json`` and write ``report.md``. Returns provider count."""
    results: list[dict] = []
    if json_path.exists():
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                results = data
        except json.JSONDecodeError:
            results = []
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(results), encoding="utf-8")
    return len(results)
