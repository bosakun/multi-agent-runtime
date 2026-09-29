"""Read-only failure audit. Does not evaluate answers, compare conditions, or use a network."""

import hashlib
import json
from pathlib import Path
from typing import Any


def read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Expected an object in the saved operational artifact")
    return value


def summarize(phase: Path) -> dict[str, Any]:
    """Keep unknown failed usage separate from the measured successful-call subtotal."""
    phase = phase.resolve()
    data = read(phase / "results.json")
    metadata, records = data["metadata"], data["records"]
    calls = []
    for path in sorted((phase / "call-journal").glob("*.json")):
        call = read(path)
        config = call["request"]["config"]
        response = call.get("response")
        usage = response.get("usage", {}) if response else {}
        tokens = usage.get("output_tokens")
        limit = config["max_output_tokens"]
        calls.append(
            {
                "journal": str(path.relative_to(phase)),
                "run_id": call["run_id"],
                "agent_id": call["agent_id"],
                "error": call["error"],
                "latency_seconds": call["latency_ms"] / 1000,
                "input_tokens": usage.get("input_tokens"),
                "generated_tokens": tokens,
                "declared_limit": limit,
                "reported_limit_headroom": limit - tokens if tokens is not None else None,
                "near_limit": tokens >= 0.95 * limit if tokens is not None else None,
                "backend_request": call.get("backend_request"),
            }
        )
    failures = []
    record_statuses = []
    for record in records:
        record_statuses.append(
            {
                "task_id": record["task_id"],
                "condition": record["condition"],
                "status": record["status"],
                "errors": record["errors"],
                "model_calls": record["metrics"]["model_calls"],
            }
        )
        if record["status"] == "succeeded" and not record["errors"]:
            continue
        trace = (phase / record["trace_file"]).resolve()
        if not trace.is_relative_to(phase / "traces"):
            raise ValueError("Trace path escapes the saved phase")
        state = read(trace)["run"]["state"]
        failed_nodes = []
        for agent_run in state["agent_runs"]:
            if agent_run["status"] != "failed":
                continue
            result = agent_run.get("result") or {}
            failed_nodes.append(
                {
                    "node_id": agent_run["node_id"],
                    "error": result.get("error"),
                    "attempts": agent_run["attempts"],
                    "latency_seconds": agent_run["latency_ms"] / 1000,
                }
            )
        failures.append(
            {
                "task_id": record["task_id"],
                "condition": record["condition"],
                "run_id": record["run_id"],
                "errors": record["errors"],
                "trace": record["trace_file"],
                "run_latency_seconds": record["metrics"]["latency_ms"] / 1000,
                "failed_nodes": failed_nodes,
                "synthesizer_executed": any(
                    call["run_id"] == record["run_id"] and call["agent_id"] == "synthesizer"
                    for call in calls
                ),
            }
        )
    source_hashes = {
        str(path.relative_to(phase)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(phase.rglob("*.json"))
    }
    return {
        "kind": "operational_failure_audit; not performance analysis",
        "protocol": metadata.get("protocol_version"),
        "executed_runs": metadata["executed_runs"],
        "records": len(records),
        "budget_used_after": metadata["budget_used_after"],
        "journal_count": len(calls),
        "stopped_reason": metadata["stopped_reason"],
        "record_statuses": record_statuses,
        "failures": failures,
        "leakage": {
            key: sum(record["metrics"][key] for record in records)
            for key in ("context_leaks", "result_leaks", "gold_leaks")
        },
        "unknown_usage_calls": sum(call["generated_tokens"] is None for call in calls),
        "known_input_tokens_subtotal": sum(call["input_tokens"] or 0 for call in calls),
        "known_generated_tokens_subtotal": sum(call["generated_tokens"] or 0 for call in calls),
        "calls": calls,
        "source_json_sha256": source_hashes,
        "limitations": [
            "Old normalized journals cannot recover finish_reason or hidden reasoning lengths.",
            "Generated-token counts are not final-answer-only tokens or character counts.",
            "Unknown failed usage is not zero and subtotals are not whole-campaign usage.",
            "Near-limit flags (95%) are diagnostic heuristics, never research exclusion rules.",
        ],
    }


def save_report(phase: Path, output: Path) -> None:
    """Create a fresh report directory outside all campaigns; never overwrite artifacts."""
    output = output.resolve()
    root = Path(__file__).resolve().parents[1]
    for protected in (root / "runs", phase.resolve(), root / "freezes", root / "benchmarks"):
        if output == protected or output.is_relative_to(protected):
            raise ValueError("Diagnostic output must be outside campaigns/freezes/benchmarks")
    report = summarize(phase)
    output.mkdir(parents=True, exist_ok=False)
    with (output / "operational.json").open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    lines = [
        "# Operational audit — not a C2/C3 performance comparison",
        "",
        f"Protocol: {report['protocol']}; runs: {report['executed_runs']}; "
        f"calls: {report['budget_used_after']}; journals: {report['journal_count']}.",
        f"Stop: `{report['stopped_reason']}`.",
        "",
        f"Usage is unknown for {report['unknown_usage_calls']} call(s). "
        "Failed usage must not be replaced with zero.",
        "",
        "| Call journal | Agent | Latency s | Generated tokens | Limit | Headroom | Error |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for call in report["calls"]:
        fields = (
            call["journal"],
            call["agent_id"],
            f"{call['latency_seconds']:.2f}",
            call["generated_tokens"],
            call["declared_limit"],
            call["reported_limit_headroom"],
            call["error"],
        )
        lines.append("| " + " | ".join("unknown" if f is None else str(f) for f in fields) + " |")
    lines.extend(["", "No answer quality, gold data, model text or hidden reasoning is included."])
    with (output / "operational.md").open("x", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
