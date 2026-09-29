"""Merge immutable successful cases and explicit recovery; original inference unchanged."""

import statistics
from pathlib import Path
from typing import Any

from epistemic.analysis import COMPARISONS, holm, paired_inference
from epistemic.paths import digest
from external_benchmarks import runner as pilot
from external_benchmarks.models import PrivateGold
from external_benchmarks.provenance import file_sha256
from external_benchmarks.scoring import score
from hotpot_main import runner as main
from hotpot_reporting.report import create
from operational_diagnostics.budget_experiment import exclusive

from hotpot_recovery import runner


def combined_records(recovery: dict[str, Any]) -> list[dict[str, Any]]:
    base, previous, _ = runner.prior()
    result: list[dict[str, Any]] = (
        base["records"]
        + [r for r in previous["records"] if r["status"] == "succeeded"]
        + recovery["records"]
    )
    return result


def analyze(*, mock: bool = False) -> Path:
    target = runner.MOCK if mock else runner.CAMPAIGN / "recovery"
    input_path = target / "results.json"
    data = runner.load(input_path)
    meta = data["metadata"]
    manifest = main.verify_data()
    output = (
        runner.MOCK.parent / "hotpotqa-recovery-mock-analysis"
        if mock
        else runner.CAMPAIGN / "analysis"
    )
    if output.exists():
        raise ValueError("Analysis exists; no overwrite")
    if (
        not runner.integral(data)
        or not meta["operational_integrity"]
        or not meta["finished_at"]
        or meta["fingerprint"] != runner.fingerprint(mock)
        or meta["dataset_sha256"] != manifest["sha256"]
        or main.ledger_used(target / "budget.sqlite" if mock else runner.CAMPAIGN / "budget.sqlite")
        != 206
    ):
        raise ValueError("Require complete current-source recovery and ledger")
    if not mock:
        runner.verify_binding()
    records = combined_records(data)
    expected = {(qid, c) for qid in manifest["task_ids"] for c in meta["conditions"]}
    if (
        len(records) != 150
        or {(r["question_id"], r["condition"]) for r in records} != expected
        or sum(r["calls"] for r in records) != 510
        or any(
            r["status"] != "succeeded" or r["errors"] or any(r["audit"].values()) for r in records
        )
    ):
        raise ValueError("Cumulative 150-case / 510-successful-call grid incomplete")
    base, previous, _ = runner.prior()
    journal_roots = {
        f"{r['question_id']}:{r['condition']}": str(
            (source / "call-journal" / r["question_id"] / r["condition"]).resolve()
        )
        for source, phase in [
            (pilot.CAMPAIGN / "pilot", base["records"]),
            (
                main.CAMPAIGN / "additional",
                [r for r in previous["records"] if r["status"] == "succeeded"],
            ),
            (target, data["records"]),
        ]
        for r in phase
    }
    full_meta = {
        **meta,
        "phase": "cumulative_with_explicit_operational_recovery",
        "planned_runs": 150,
        "planned_calls": 510,
        "executed_runs": 150,
        "model_calls": 510,
        "total_reservations": 511,
        "unsuccessful_pre_dispatch_reservations": 1,
        "journal_roots": journal_roots,
        "interpretation": "MOCK RECOVERY PLUMBING WITH REAL PREFIX; NOT PERFORMANCE"
        if mock
        else "REAL HOTPOTQA CUMULATIVE EXPLORATORY COHORT WITH RECOVERY",
        "source_result_sha256": {
            str(p): file_sha256(p)
            for p in [
                pilot.CAMPAIGN / "pilot/results.json",
                main.CAMPAIGN / "additional/results.json",
                input_path,
            ]
        },
    }
    cumulative_path = output / "cumulative-results.json"
    exclusive(cumulative_path, {"metadata": full_meta, "records": records})
    indexed = {(r["question_id"], r["condition"]): r for r in records}
    fresh = manifest["task_ids"][6:]
    comparisons = {
        name: {
            "contrast": f"{a}-{b}",
            **paired_inference(
                [
                    indexed[qid, a]["metrics"]["f1"] - indexed[qid, b]["metrics"]["f1"]
                    for qid in fresh
                ],
                seed=20260928,
            ),
        }
        for name, a, b in COMPARISONS
    }
    for name, adjusted in zip(
        ["P2", "P3", "P4", "P5"],
        holm([comparisons[n]["p"] for n in ["P2", "P3", "P4", "P5"]]),
        strict=True,
    ):
        comparisons[name]["holm_secondary_p"] = adjusted
    summaries: dict[str, Any] = {}
    for label, ids in [
        ("cumulative30_exploratory", manifest["task_ids"]),
        ("fresh24_prospective", fresh),
    ]:
        gold = [
            PrivateGold.model_validate_json(
                (main.BUNDLE / "gold" / f"{qid}.json").read_text(encoding="utf-8")
            )
            for qid in ids
        ]
        summaries[label] = {}
        for condition in meta["conditions"]:
            predictions: dict[str, Any] = {"answer": {}, "sp": {}}
            for qid in ids:
                for key in predictions:
                    predictions[key].update(indexed[qid, condition]["predictions"][key])
            summaries[label][condition] = score(predictions, gold)
            exclusive(output / f"predictions-{label}-{condition}.json", predictions)
    original_failure = next(r for r in previous["records"] if r["status"] == "partial")
    recovered = indexed[runner.FAILED_QID, "C1"]
    sensitivity = {
        "question_id": runner.FAILED_QID,
        "condition": "C1",
        "original_failed_record": original_failure,
        "recovered_run_id": recovered["run_id"],
        "original_answer_f1": original_failure["metrics"]["f1"],
        "recovered_answer_f1": recovered["metrics"]["f1"],
        "fresh24_C1_answer_f1_change": (
            recovered["metrics"]["f1"] - original_failure["metrics"]["f1"]
        )
        / 24,
        "primary_C3_minus_C2_unchanged_by_C1_recovery": True,
        "interpretation": (
            "Descriptive operational-failure sensitivity, not a new significance test"
        ),
    }
    interaction = [
        (indexed[qid, "C4"]["metrics"]["f1"] - indexed[qid, "C3"]["metrics"]["f1"])
        - (indexed[qid, "C2"]["metrics"]["f1"] - indexed[qid, "C1"]["metrics"]["f1"])
        for qid in fresh
    ]
    result = {
        "metadata": full_meta,
        "summaries": summaries,
        "fresh24_comparisons": comparisons,
        "fresh24_descriptive_interaction": {
            "n_questions": 24,
            "mean_difference": statistics.mean(interaction),
            "task_differences": interaction,
            "inference": "descriptive only",
        },
        "operational_recovery_sensitivity": sensitivity,
        "source_files": runner.sources(),
        "analysis_controls": runner.controls(),
        "limitations": [
            "Six Pilot questions predate the full plan; cumulative30 is exploratory.",
            "Inference uses fresh24 only; entity dependence may invalidate iid intervals.",
            "Length-selected dev subset, not full benchmark or contamination-free score.",
            "Single model, temperature0, one repetition; no broad generalization.",
            "One explicitly approved recovery after Windows pre-dispatch journal failure.",
        ],
    }
    result["analysis_sha256"] = digest(result)
    exclusive(output / "analysis.json", result)
    create(cumulative_path, main.BUNDLE, output / "descriptive")
    lines = [
        "# " + full_meta["interpretation"],
        "",
        "150 cases / 510 successful model calls / 511 reservations "
        "(1 original pre-dispatch failure).",
        "",
    ]
    for label, values in summaries.items():
        lines.extend(
            [
                "## " + label,
                "",
                "| Condition | Answer EM | Answer F1 | Support F1 | Joint F1 |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for condition, metrics in values.items():
            lines.append(
                f"| {condition} | {metrics['em']:.3f} | {metrics['f1']:.3f} "
                f"| {metrics['sp_f1']:.3f} | {metrics['joint_f1']:.3f} |"
            )
        lines.append("")
    lines.extend(
        [
            "## Fresh24 paired answer-F1 comparisons",
            "",
            "| Contrast | Mean delta | CI95 | p | Secondary Holm p |",
            "|---|---:|---|---:|---|",
        ]
    )
    for value in comparisons.values():
        lines.append(
            f"| {value['contrast']} | {value['mean_difference']:.4f} | {value['ci95']} "
            f"| {value['p']:.4f} | {value.get('holm_secondary_p', 'primary')} |"
        )
    lines.extend(
        [
            "",
            f"Descriptive interaction (C4-C3)-(C2-C1): {statistics.mean(interaction):.4f}",
            f"Original failed C1 F1={sensitivity['original_answer_f1']}; "
            f"recovered F1={sensitivity['recovered_answer_f1']}.",
            "Primary contrast C3-C2 is unaffected by C1 recovery.",
            "",
            *result["limitations"],
        ]
    )
    with (output / "summary.md").open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines) + "\n")
    return output / "analysis.json"
