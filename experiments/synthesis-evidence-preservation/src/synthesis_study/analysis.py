"""Official paired scoring and transparent completion audit after all generation."""

import csv
import io
import json
import random
import statistics
from pathlib import Path
from typing import Any

from external_benchmarks.models import PrivateGold
from external_benchmarks.scoring import score
from hotpot_reporting.report import bar_svg

from synthesis_study.io import REPO, STUDY, digest, exclusive, file_hash, read
from synthesis_study.runner import citations, source_preserved, validate_response, verify_seal


def paired(values: list[float], clusters: list[list[int]] | None = None) -> dict[str, Any]:
    rng = random.Random(20260930)
    groups = clusters if clusters is not None else [[index] for index in range(len(values))]
    result = {
        "mean_difference": statistics.mean(values),
        "improved": sum(v > 0 for v in values),
        "tied": sum(v == 0 for v in values),
        "worse": sum(v < 0 for v in values),
        "question_count": len(values),
        "cluster_count": len(groups),
        "draws": 10000,
        "interpretation": "exploratory_conditional",
    }
    if clusters is not None and len(groups) < 2:
        return {**result, "ci95": None, "reason": "one_connected_component"}
    draws = []
    for _ in range(10000):
        sample = [index for group in rng.choices(groups, k=len(groups)) for index in group]
        draws.append(statistics.mean(values[index] for index in sample))
    draws.sort()
    return {**result, "ci95": [draws[249], draws[9749]]}


def components(ids: list[str], questions: dict[str, Any]) -> list[list[int]]:
    titles = [{s["title"] for s in questions[qid]["sentences"]} for qid in ids]
    unseen = set(range(len(ids)))
    groups = []
    while unseen:
        reached = {min(unseen)}
        frontier = set(reached)
        while frontier:
            item = frontier.pop()
            neighbors = {other for other in unseen - reached if titles[item] & titles[other]}
            reached.update(neighbors)
            frontier.update(neighbors)
        unseen -= reached
        groups.append(sorted(reached))
    return groups


def analyze(campaign: Path) -> dict[str, Any]:
    data = read(campaign / "results.json")
    manifest_path = STUDY / "data/replay-inputs/manifest.json"
    manifest = read(manifest_path)
    if data["provider"] == "real":
        verify_seal()
    if (
        data["status"] != "completed"
        or data["reservations"] != 81
        or len(data["records"]) != 81
        or data["input_manifest_sha256"] != file_hash(manifest_path)
    ):
        raise ValueError("Incomplete campaign; do not score a partial cohort")
    expected = {(p["phase"], p["qid"], p["arm"]): p for p in manifest["calls"]}
    indexed = {(r["phase"], r["qid"], r["arm"]): r for r in data["records"]}
    if set(expected) != set(indexed) or len(indexed) != 81 or data["new_worker_calls"] != 0:
        raise ValueError("Case grid differs from manifest")
    preserve = source_preserved(manifest)
    if not preserve["passed"]:
        raise ValueError("Historical source drift")
    spec = manifest["spec"]
    qids = spec["main_question_ids"]
    public = {qid: read(REPO / spec["public_data_root"] / f"{qid}.json") for qid in qids}
    gold = {
        qid: PrivateGold.model_validate(
            read(REPO / spec["private_evaluation_root"] / f"{qid}.json")
        )
        for qid in qids
    }
    aggregates, rows = {}, []
    output_root = STUDY / "reports" / campaign.name
    scores_by_cell = {}
    for arm in spec["arms"]:
        predictions: dict[str, dict[str, Any]] = {"answer": {}, "sp": {}}
        for qid in qids:
            record = indexed["main", qid, arm]
            planned = expected["main", qid, arm]
            if (
                record["status"] != "succeeded"
                or digest(record["request"]) != planned["body_sha256"]
                or record["input_tokens"] != planned["prompt_tokens"]
            ):
                raise ValueError("Request/status/count mismatch")
            sentence_map = {
                s["id"]: [s["title"], s["sentence_index"]] for s in public[qid]["sentences"]
            }
            if not citations(record["output"]).issubset(set(planned["allowed_ids"])):
                raise ValueError("Output citation violation")
            single = {
                "answer": {qid: record["output"]["answer"]},
                "sp": {
                    qid: [
                        sentence_map[sid] for sid in dict.fromkeys(record["output"]["evidence_ids"])
                    ]
                },
            }
            metrics = score(single, [gold[qid]])
            predictions["answer"].update(single["answer"])
            predictions["sp"].update(single["sp"])
            scores_by_cell[qid, arm] = metrics
            rows.append(
                {
                    "question_id": qid,
                    "arm": arm,
                    "answer": record["output"]["answer"],
                    **metrics,
                    "input_tokens": record["input_tokens"],
                    "output_tokens": record["output_tokens"],
                    "latency_seconds": record["latency_seconds"],
                }
            )
        aggregates[arm] = score(predictions, list(gold.values()))
        exclusive(output_root / f"predictions-{arm}.json", predictions)
    comparisons = {}
    groups = components(qids, public)
    for positive, negative in [("B", "A"), ("B", "C"), ("C", "A")]:
        differences = [
            scores_by_cell[qid, positive]["f1"] - scores_by_cell[qid, negative]["f1"]
            for qid in qids
        ]
        comparisons[f"{positive}-{negative}"] = {
            **paired(differences),
            "cluster_sensitivity": paired(differences, groups),
            "per_question": dict(zip(qids, differences, strict=True)),
        }
    controls = [
        abs(indexed["main", qid, "B"]["input_tokens"] - indexed["main", qid, "C"]["input_tokens"])
        / indexed["main", qid, "B"]["input_tokens"]
        for qid in qids
    ]
    if max(controls) > 0.05:
        raise ValueError("Native input token control failed")
    audit = read(STUDY / "reports/source-audit/audit.json")
    import sqlite3
    from contextlib import closing

    with closing(
        sqlite3.connect(f"file:{(campaign / 'replay.sqlite').as_posix()}?mode=ro", uri=True)
    ) as db:
        event_count = int(db.execute("SELECT COUNT(*) FROM events").fetchone()[0])
    with closing(
        sqlite3.connect(f"file:{(campaign / 'budget.sqlite').as_posix()}?mode=ro", uri=True)
    ) as db:
        reservation_count = int(db.execute("SELECT COUNT(*) FROM calls").fetchone()[0])
    if (
        event_count != 162
        or reservation_count != 81
        or len(list((campaign / "call-journal").glob("*.json"))) != 81
        or len(list((campaign / "native-observations").glob("*.json"))) != 81
    ):
        raise ValueError("Database/journal/ledger grid mismatch")
    # Validate every smoke and main observation, not only the scored 72 cells.
    for record in data["records"]:
        number = record["number"]
        if read(campaign / "call-journal" / f"{number:04}.json") != record:
            raise ValueError("Canonical journal differs from terminal result")
        observation = read(campaign / "native-observations" / f"{number:04}.json")
        if (
            observation["done"] is not True
            or observation["finish_reason"] != "stop"
            or observation["thinking_chars"] != 0
            or observation["input_tokens"] != record["input_tokens"]
            or observation["output_tokens"] != record["output_tokens"]
        ):
            raise ValueError("Native observation differs from terminal result")
        import hashlib

        if (
            observation["final_content_sha256"]
            != hashlib.sha256(record["final_content"].encode()).hexdigest()
        ):
            raise ValueError("Native final content checksum mismatch")
        restored_output = validate_response(
            {
                "done": True,
                "done_reason": "stop",
                "message": {"content": record["final_content"], "thinking": ""},
                "prompt_eval_count": record["input_tokens"],
                "eval_count": record["output_tokens"],
            },
            expected[record["phase"], record["qid"], record["arm"]],
        )
        if restored_output != record["output"]:
            raise ValueError("Final parsed output differs from preserved native content")
    report = {
        "study_id": spec["study_id"],
        "provider": data["provider"],
        "model_comparison_completed": data["provider"] == "real",
        "full_research_completed": False,
        "independent_human_review": "pending",
        "main_questions": 24,
        "scored_cases": 72,
        "smoke_calls": 9,
        "successful_calls": 81,
        "reservations": 81,
        "new_worker_calls": 0,
        "conditions": aggregates,
        "comparisons": comparisons,
        "max_native_B_C_relative_input_difference": max(controls),
        "cluster_sizes": [len(g) for g in groups],
        "source_preservation": preserve,
        "source_audit_questions": audit["questions"],
        "source_transfer_mismatches": audit["transfer_mismatches_after_schema_validation"],
    }
    previous = read(REPO / spec["source_files"][2]["path"])
    previous_scores = {
        r["question_id"]: r["metrics"]["f1"] for r in previous["records"] if r["condition"] == "C3"
    }
    report["historical_C3_reexecution"] = {
        "mean_A_minus_historical_C3": statistics.mean(
            scores_by_cell[qid, "A"]["f1"] - previous_scores[qid] for qid in qids
        ),
        "interpretation": "descriptive_prompt_and_reexecution_difference",
    }
    exclusive(output_root / "analysis.json", report)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    exclusive(output_root / "cases.csv", buffer.getvalue(), text=True)
    heading = (
        "MOCK PLUMBING — NOT MODEL PERFORMANCE"
        if data["provider"] == "mock"
        else "REAL FIXED-WORKER EXPLORATORY COMPARISON"
    )
    lines = [
        f"# {heading}",
        "",
        "24 previously observed questions; smoke excluded from scores.",
        "",
        "| Arm | Answer F1 | Answer EM | Support F1 | Joint F1 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    lines.extend(
        f"| {arm} | {m['f1']:.4f} | {m['em']:.4f} | {m['sp_f1']:.4f} | {m['joint_f1']:.4f} |"
        for arm, m in aggregates.items()
    )
    lines.extend(
        [
            "",
            "| Comparison | Paired mean F1 difference | Conditional CI95 |",
            "| --- | ---: | --- |",
        ]
    )
    lines.extend(
        f"| {name} | {value['mean_difference']:.4f} | {value['ci95']} |"
        for name, value in comparisons.items()
    )
    lines.extend(
        [
            "",
            "81 successful synthesizer calls / 81 reservations / 0 new worker calls.",
            "Independent human review pending; full research completion is not established.",
            "Same-token input control is not equal total compute. "
            "Single model, one repetition, observed length-selected questions.",
        ]
    )
    exclusive(output_root / "summary.md", "\n".join(lines) + "\n", text=True)
    for filename, title, series, unit in [
        (
            "answer-f1.svg",
            "Answer F1",
            {arm: metrics["f1"] for arm, metrics in aggregates.items()},
            "0–1",
        ),
        (
            "input-tokens.svg",
            "Mean native input tokens",
            {
                arm: statistics.mean(row["input_tokens"] for row in rows if row["arm"] == arm)
                for arm in spec["arms"]
            },
            "tokens",
        ),
        (
            "latency.svg",
            "Mean model-call latency",
            {
                arm: statistics.mean(row["latency_seconds"] for row in rows if row["arm"] == arm)
                for arm in spec["arms"]
            },
            "seconds",
        ),
    ]:
        exclusive(
            output_root / filename,
            bar_svg(
                title, series, "Exploratory existing24; independent human review pending", unit=unit
            ),
            text=True,
        )
    # Anonymous new-answer review packets; no condition/score visible in public packet.
    review_rows = []
    for row in rows:
        qid, arm = row["question_id"], row["arm"]
        code = "new-" + digest({"qid": qid, "arm": arm, "seed": 20260930})[:12]
        record = indexed["main", qid, arm]
        packet = {
            "case_code": code,
            "question": public[qid]["question"],
            "public_sentences": public[qid]["sentences"],
            "synthesis_input": json.loads(record["request"]["messages"][1]["content"]),
            "output": record["output"],
        }
        exclusive(output_root / "review/public" / f"{code}.json", packet)
        exclusive(
            output_root / "review/private" / f"{code}.json",
            {
                "case_code": code,
                "qid": qid,
                "arm": arm,
                "gold": gold[qid].model_dump(mode="json"),
                "metrics": scores_by_cell[qid, arm],
            },
        )
        for reviewer in ["reviewer_1", "reviewer_2"]:
            review_rows.append(
                {
                    "case_code": code,
                    "reviewer_id": reviewer,
                    "final_supported": "",
                    "rationale": "",
                    "confidence": "",
                    "reviewed_at": "",
                }
            )
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(review_rows[0]))
    writer.writeheader()
    writer.writerows(review_rows)
    exclusive(output_root / "review/blank-final-review.csv", buffer.getvalue(), text=True)
    exclusive(
        output_root / "completion-audit.json",
        {
            "provider": data["provider"],
            "passed_pipeline": True,
            "passed_model_comparison": data["provider"] == "real",
            "passed_full_research": False,
            "reason": "independent_human_review_pending",
            "successful_calls": 81,
            "main_cells": 72,
            "ledger_reservations": 81,
            "events": event_count,
            "canonical_journals": 81,
            "native_observations": 81,
            "historical_preservation": preserve,
            "analysis_sha256": file_hash(output_root / "analysis.json"),
        },
    )
    return {
        "report": str(output_root),
        "conditions": aggregates,
        "comparisons": {name: value["mean_difference"] for name, value in comparisons.items()},
        "human_review": "pending",
    }
