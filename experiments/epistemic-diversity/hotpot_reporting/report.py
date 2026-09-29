"""Recompute official scores and inspect saved journals; never contact a model."""

import csv
import hashlib
import json
import statistics
from itertools import combinations
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from bounded_pilot.contract import bounded_schema, validate_citation_lengths
from epistemic.conditions import configurations
from external_benchmarks.conditions import build
from external_benchmarks.dataset import load_public, supporting_pairs
from external_benchmarks.models import PrivateGold
from external_benchmarks.provenance import file_sha256, verify_bundle
from external_benchmarks.scoring import score
from operational_diagnostics.budget_experiment import exclusive

from app.llm.provider import ModelRequest


def citations(value: Any) -> set[str]:
    """Count citation IDs, not semantically validated claims."""
    result: set[str] = set()
    if isinstance(value, dict):
        ids = value.get("evidence_ids", [])
        if isinstance(ids, list):
            result.update(item for item in ids if isinstance(item, str))
        for nested in value.values():
            result.update(citations(nested))
    elif isinstance(value, list):
        for nested in value:
            result.update(citations(nested))
    return result


def diversity(sets: list[set[str]], gold: set[str], *, single: bool) -> dict[str, Any]:
    union = set().union(*sets)
    summed = sum(map(len, sets))
    pairs = [len(a & b) / len(a | b) for a, b in combinations(sets, 2) if a | b]
    return {
        "worker_citation_union": len(union),
        "worker_gold_support_recall": len(union & gold) / len(gold) if gold else None,
        "worker_citation_precision": len(union & gold) / len(union) if union else 0.0,
        "worker_citation_redundancy": 1 - len(union) / summed if summed and not single else None,
        "worker_citation_jaccard": statistics.mean(pairs) if pairs and not single else None,
        "worker_unique_citation_fraction": (
            sum(sum(eid in group for group in sets) == 1 for eid in union) / len(union)
            if union and not single
            else None
        ),
    }


def bar_svg(title: str, series: dict[str, float], note: str, *, unit: str = "") -> str:
    height = 110 + 42 * len(series)
    maximum = max(series.values(), default=0) or 1
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="850" height="{height}" '
        f'viewBox="0 0 850 {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="20" y="28" font-family="sans-serif" font-size="19">{escape(title)}</text>',
        f'<text x="20" y="51" font-family="sans-serif" font-size="12">{escape(note)}</text>',
    ]
    for index, (label, value) in enumerate(series.items()):
        y = 70 + index * 42
        parts.extend(
            [
                f'<text x="20" y="{y + 19}" font-family="sans-serif">{escape(label)}</text>',
                f'<rect x="70" y="{y}" width="{600 * value / maximum:.2f}" height="25" '
                'fill="#2563eb"/>',
                f'<text x="{82 + 600 * value / maximum:.2f}" y="{y + 19}" '
                f'font-family="sans-serif">{value:.3f}{escape(unit)}</text>',
            ]
        )
    parts.append("</svg>")
    return "\n".join(parts)


def create(input_path: Path, bundle: Path, output: Path) -> Path:
    if output.exists():
        raise ValueError("Report output exists; no overwrite")
    data = json.loads(input_path.read_text(encoding="utf-8"))
    meta, records = data["metadata"], data["records"]
    manifest = verify_bundle(bundle)
    expected = {(qid, condition) for qid in meta["task_ids"] for condition in meta["conditions"]}
    if (
        not meta.get("finished_at")
        or not meta.get("operational_integrity")
        or meta.get("stopped_reason")
        or len(records) != meta["planned_runs"]
        or {(r["question_id"], r["condition"]) for r in records} != expected
        or len(expected) != len(records)
        or meta["model_calls"] != meta["planned_calls"]
        or meta["dataset_sha256"] != manifest["sha256"]
    ):
        raise ValueError("Require a complete, terminal, unchanged-data cohort")
    questions = {q.id: q for q in load_public(bundle, meta["task_ids"])}
    gold = {
        qid: PrivateGold.model_validate_json(
            (bundle / "gold" / f"{qid}.json").read_text(encoding="utf-8")
        )
        for qid in meta["task_ids"]
    }
    label = (
        meta.get("interpretation", "REAL HOTPOTQA DEV")
        if meta["provider"] == "real"
        else "MOCK - NOT LLM RESULTS"
    )
    review = [
        f"# {label}: saved-output review",
        "",
        "Generated inspection, not independent human validation.",
        "",
    ]
    descriptive: list[dict[str, Any]] = []
    input_hashes = {str(input_path): file_sha256(input_path)}
    for record in records:
        qid, condition = record["question_id"], record["condition"]
        if record["status"] != "succeeded" or record["errors"] or any(record["audit"].values()):
            raise ValueError("Invalid runtime/access record")
        official = score(record["predictions"], [gold[qid]])
        if official != record["metrics"]:
            raise ValueError("Stored metrics differ from official recomputation")
        journal = Path(
            meta.get("journal_roots", {}).get(
                f"{qid}:{condition}", str(input_path.parent / "call-journal" / qid / condition)
            )
        )
        calls = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(journal.glob("*.json"))]
        if len(calls) != record["calls"] or any(
            call["error"] or not call["response"] for call in calls
        ):
            raise ValueError("Incomplete call journal")
        input_hashes.update({str(p): file_sha256(p) for p in sorted(journal.glob("*.json"))})
        workers = [call for call in calls if call["agent_id"].startswith("worker_")]
        config = next(c for c in configurations() if c.id == condition)
        _, agents, _, _ = build(questions[qid], config, mock=meta["provider"] == "mock")
        sentences = {s.id: s for s in questions[qid].sentences}
        for call in calls:
            request = ModelRequest.model_validate(call["request"])
            context = request.context
            agent = agents[call["agent_id"]]
            if (
                context.task != questions[qid].question
                or context.inputs
                or {k.id for k in context.knowledge} != set(agent.context.knowledge_ids)
                or request.instruction != agent.instruction
                or request.output_schema != bounded_schema(request.output_schema, context)
            ):
                raise ValueError("Saved input policy/schema drift")
            for item in context.knowledge:
                sentence = sentences[item.id]
                if json.loads(item.content) != {
                    "title": sentence.title,
                    "sentence_index": sentence.sentence_index,
                    "text": sentence.text,
                }:
                    raise ValueError("Saved public sentence drift")
            output_ids = citations(call["response"]["output"])
            if not output_ids.issubset(context.evidence_scope()):
                raise ValueError("Saved output cites unauthorized evidence")
            validate_citation_lengths(call["response"]["output"], len(context.evidence_scope()))
            if meta["provider"] == "real":
                wire = call["backend_request"]
                if (
                    not wire
                    or wire["api"] != "/api/chat"
                    or wire["think"] is not False
                    or wire["options"] != {"temperature": 0, "num_predict": 4096, "num_ctx": 8192}
                    or wire["allowed_evidence_ids"] != sorted(context.evidence_scope())
                    or wire["citation_max_items"] != len(context.evidence_scope())
                ):
                    raise ValueError("Native wire audit/control drift")
                observation_path = (
                    journal.parents[2]
                    / "http-observations"
                    / f"{call['run_id']}_{call['agent_id']}.json"
                )
                observation = json.loads(observation_path.read_text(encoding="utf-8"))
                if (
                    observation["finish_reason"] != "stop"
                    or observation["thinking_chars"]
                    or observation["input_tokens"] > 4096
                    or observation["generated_tokens"] > 4096
                ):
                    raise ValueError("Native completion/context guard failed")
                input_hashes[str(observation_path)] = file_sha256(observation_path)
        groups = [citations(call["response"]["output"]) for call in workers]
        support_ids = {
            s.id
            for s in questions[qid].sentences
            if (s.title, s.sentence_index) in set(gold[qid].supporting_facts)
        }
        usage = record["usage"]
        if sum(call["response"]["usage"]["model_calls"] for call in calls) != record["calls"]:
            raise ValueError("Journal usage/call count mismatch")
        raw = [call["request"]["context"]["knowledge"] for call in workers]
        descriptive.append(
            {
                "question_id": qid,
                "condition": condition,
                **official,
                **diversity(groups, support_ids, single=condition == "C0"),
                "input_tokens": usage["input_tokens"],
                "output_tokens": usage["output_tokens"],
                "model_calls": record["calls"],
                "cost_usd": None,
                "call_latency_seconds": sum(call["latency_ms"] for call in calls) / 1000,
                "raw_sentence_exposures": sum(map(len, raw)),
                "raw_sentence_union": len({item["id"] for group in raw for item in group}),
                "audit_violations": sum(record["audit"].values()),
            }
        )
        review.extend(
            [
                f"## {qid} / {condition}",
                "",
                questions[qid].question,
                "",
                f"Gold answer: {gold[qid].answer}",
                f"Prediction: {record['predictions']['answer'][qid]}",
                f"Answer EM/F1: {official['em']:.3f} / {official['f1']:.3f}",
                f"Gold support: {json.dumps(gold[qid].supporting_facts, ensure_ascii=False)}",
                "Predicted support: "
                + json.dumps(record["predictions"]["sp"][qid], ensure_ascii=False),
                "",
            ]
        )
        for worker in workers:
            result = worker["response"]["output"]
            review.extend(
                [
                    f"### {worker['agent_id']}",
                    "",
                    "```json",
                    json.dumps(result, ensure_ascii=False, indent=2),
                    "```",
                    "",
                ]
            )
            referenced = citations(result)
            for sentence in questions[qid].sentences:
                if sentence.id in referenced:
                    review.append(
                        f"- {sentence.id} [{sentence.title}, {sentence.sentence_index}]: "
                        f"{sentence.text}"
                    )
            # This mapping uses public sentence metadata only.
            supporting_pairs(questions[qid], sorted(referenced))
            review.append("")
    summaries: dict[str, Any] = {}
    for condition in meta["conditions"]:
        cells = [r for r in descriptive if r["condition"] == condition]
        summaries[condition] = {
            key: statistics.mean([r[key] for r in cells if r[key] is not None])
            if any(r[key] is not None for r in cells)
            else None
            for key in descriptive[0]
            if key not in {"question_id", "condition"}
        }
    report = {
        "label": label,
        "input_hashes": input_hashes,
        "dataset_sha256": manifest["sha256"],
        "report_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "summaries": summaries,
        "records": descriptive,
        "limits": [
            "Public-length-selected dev subset, not a full benchmark or contamination-free test.",
            "Citation overlap/uniqueness is mechanical under disjoint access, "
            "not cognitive diversity.",
            "Gold-support citation recall does not validate the accompanying semantic claim.",
            "These diagnostics were added after Pilot launch; descriptive, not new endpoints.",
            "Call latency excludes runtime/checkpoint overhead; no pricing, cost is unknown.",
        ],
    }
    exclusive(output / "report.json", report)
    with (output / "cases.csv").open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(descriptive[0]))
        writer.writeheader()
        writer.writerows(descriptive)
    (output / "saved-output-review.md").write_text("\n".join(review), encoding="utf-8")
    contrasts = []
    indexed = {(r["question_id"], r["condition"]): r for r in records}
    for qid in meta["task_ids"]:
        if "C2" not in meta["conditions"] or "C3" not in meta["conditions"]:
            continue
        c2, c3 = indexed[qid, "C2"], indexed[qid, "C3"]
        if c2["metrics"]["em"] != c3["metrics"]["em"]:
            contrasts.append(
                {"question_id": qid, "C2_EM": c2["metrics"]["em"], "C3_EM": c3["metrics"]["em"]}
            )
    exclusive(output / "discordant-C2-C3.json", {"cases": contrasts, "not_found": not contrasts})
    note = f"{label}; n={len(meta['task_ids'])} per condition; selected dev subset"
    for filename, title, metric in [
        ("answer-f1", "Official answer F1", "f1"),
        ("support-f1", "Official supporting-fact F1", "sp_f1"),
        ("input-tokens", "Mean input tokens (unequal aggregate context)", "input_tokens"),
        ("call-latency", "Mean summed model-call seconds (not end-to-end)", "call_latency_seconds"),
        (
            "citation-overlap",
            "Worker citation Jaccard (mechanical, descriptive)",
            "worker_citation_jaccard",
        ),
        (
            "access-audit",
            "Observed access-audit violations (not security proof)",
            "audit_violations",
        ),
    ]:
        series = {
            key: value[metric] for key, value in summaries.items() if value[metric] is not None
        }
        (output / f"{filename}.svg").write_text(bar_svg(title, series, note), encoding="utf-8")
    return output / "report.json"
