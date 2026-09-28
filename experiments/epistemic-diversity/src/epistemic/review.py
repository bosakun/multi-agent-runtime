"""Human-readable inspection, with tentative labels rather than invented causes."""

import json
from pathlib import Path
from typing import Any


def candidate_patterns(record: dict[str, Any]) -> list[str]:
    m = record["metrics"]
    candidates = []
    if (m.get("evidence_redundancy") or 0) > 0.4:
        candidates.append("all agents repeat same evidence")
    if (m.get("claim_unique") or 0) > 0:
        candidates.append("useful unique contribution")
    if m.get("worker_contradictions", 0):
        candidates.append("conflicting interpretations")
    if m.get("worker_evidence_coverage", 0) > m.get("gold_claim_coverage", 0):
        candidates.append("synthesis failure (candidate)")
    if m.get("unsupported_claims", 0):
        candidates.append("hallucinated bridge claim (candidate; inspect support)")
    drops = [
        x["drop"] for x in record.get("diagnostics", {}).get("marginal_final_claim_support", [])
    ]
    if len(drops) > 1 and sum(d > 0 for d in drops) == 1:
        candidates.append("dominant agent effect (provenance proxy)")
    return candidates


def human_review(data: dict[str, Any], path: Path) -> None:
    lines = [
        "# Pilot human review",
        "",
        data["metadata"]["interpretation"],
        "",
        "These are executed outputs. Automatic tags are review candidates, not causal conclusions.",
        "Gold appears ONLY in this evaluator-side report, never in a model request.",
        "",
    ]
    for record in sorted(
        data["records"], key=lambda r: (r["task_id"], r["condition"], r["repetition"])
    ):
        review = record.get("human_review", {})
        lines += [
            f"## {record['task_id']} / {record['condition']} / repetition {record['repetition']}",
            "",
            f"Status: {record['status']}; run: {record['run_id']}",
            "",
            "### Task",
            "",
            review.get("task", "See originating v1 trace."),
            "",
            "### Agent outputs / Evidence IDs used",
            "",
            "```json",
            json.dumps(review.get("workers", []), indent=2),
            "```",
            "",
            "### Final output",
            "",
            "```json",
            json.dumps(record["output"], indent=2),
            "```",
            "",
            "### Gold",
            "",
            "```json",
            json.dumps(review.get("gold", {}), indent=2),
            "```",
            "",
            "### Metrics / errors / assignment",
            "",
            "```json",
            json.dumps(
                {
                    "metrics": record["metrics"],
                    "errors": record["errors"],
                    "assignment": record["assignment"],
                    "diagnostics": record["diagnostics"],
                },
                indent=2,
            ),
            "```",
            "",
            f"Candidate patterns: {candidate_patterns(record)}",
            "",
            "Human checks: [ ] missing global context [ ] role bias [ ] partition-induced failure",
            "[ ] synthesis failure [ ] hallucinated bridge [ ] dominant-agent interpretation",
            "Reviewer / evidence / competing explanation / confidence: TODO",
            "",
        ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
