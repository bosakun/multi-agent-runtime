"""Exact official summaries and fresh-question paired inference, never model generation."""

import json
from pathlib import Path
from typing import Any

from epistemic.analysis import COMPARISONS, holm, paired_inference
from epistemic.paths import digest
from external_benchmarks.models import PrivateGold
from external_benchmarks.provenance import file_sha256
from external_benchmarks.scoring import score
from hotpot_reporting.report import create
from operational_diagnostics.budget_experiment import exclusive

from hotpot_main import runner


def analyze(input_path: Path, output: Path) -> Path:
    if output.exists():
        raise ValueError("Analysis exists; no overwrite")
    data = json.loads(input_path.read_text(encoding="utf-8"))
    meta = data["metadata"]
    manifest = runner.verify_data()
    mock = meta["provider"] == "mock"
    base_path, base = runner.base_gate(mock)
    if (
        not runner.integral(data, manifest)
        or not meta.get("operational_integrity")
        or not meta.get("finished_at")
        or meta["dataset_sha256"] != manifest["sha256"]
        or meta["fingerprint"] != runner.fingerprint(mock)
        or meta["pilot_result_sha256"] != file_sha256(base_path)
        or runner.ledger_used(
            input_path.parent / "budget.sqlite" if mock else runner.CAMPAIGN / "budget.sqlite"
        )
        != 456
    ):
        raise ValueError("Require complete unchanged-source additional cohort and ledgers")
    if not mock:
        runner.verify_binding()
    combined = base["records"] + data["records"]
    expected = {(qid, c) for qid in manifest["task_ids"] for c in meta["conditions"]}
    if len(combined) != 150 or {(r["question_id"], r["condition"]) for r in combined} != expected:
        raise ValueError("Cumulative 150-case grid incomplete or duplicated")
    if sum(r["calls"] for r in combined) != 510:
        raise ValueError("Cumulative call ledger mismatch")
    journal_roots = {
        f"{r['question_id']}:{r['condition']}": str(
            (source / "call-journal" / r["question_id"] / r["condition"]).resolve()
        )
        for source, records in (
            (base_path.parent, base["records"]),
            (input_path.parent, data["records"]),
        )
        for r in records
    }
    full_meta = {
        **meta,
        "phase": "cumulative",
        "planned_runs": 150,
        "planned_calls": 510,
        "executed_runs": 150,
        "model_calls": 510,
        "journal_roots": journal_roots,
        "interpretation": "MOCK VALIDATION, NOT MODEL PERFORMANCE"
        if mock
        else "REAL HOTPOTQA CUMULATIVE EXPLORATORY COHORT",
        "source_result_sha256": {
            str(base_path): file_sha256(base_path),
            str(input_path): file_sha256(input_path),
        },
    }
    cumulative_path = output / "cumulative-results.json"
    exclusive(cumulative_path, {"metadata": full_meta, "records": combined})
    new_ids = manifest["task_ids"][6:]
    indexed = {(r["question_id"], r["condition"]): r for r in combined}
    comparisons: dict[str, Any] = {}
    for name, a, b in COMPARISONS:
        differences = [
            indexed[qid, a]["metrics"]["f1"] - indexed[qid, b]["metrics"]["f1"] for qid in new_ids
        ]
        comparisons[name] = {"contrast": f"{a}-{b}", **paired_inference(differences, seed=20260928)}
    adjusted = holm([comparisons[name]["p"] for name in ["P2", "P3", "P4", "P5"]])
    for name, p in zip(["P2", "P3", "P4", "P5"], adjusted, strict=True):
        comparisons[name]["holm_secondary_p"] = p
    summaries: dict[str, Any] = {}
    for label, ids in (
        ("cumulative30_exploratory", manifest["task_ids"]),
        ("fresh24_prospective", new_ids),
    ):
        gold = [
            PrivateGold.model_validate_json(
                (runner.BUNDLE / "gold" / f"{qid}.json").read_text(encoding="utf-8")
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
    result = {
        "metadata": full_meta,
        "summaries": summaries,
        "fresh24_comparisons": comparisons,
        "source_files": runner.sources(),
        "analysis_controls": runner.controls(),
        "limitations": [
            "Six Pilot questions preceded this plan; cumulative30 is exploratory.",
            "Inference uses 24 new questions; shared entities may invalidate iid intervals.",
            "Length-limited dev subset, not full benchmark or contamination-free score.",
            "One temperature0 repetition; no broad model or stochastic generalization.",
        ],
    }
    result["analysis_sha256"] = digest(result)
    exclusive(output / "analysis.json", result)
    create(cumulative_path, runner.BUNDLE, output / "descriptive")
    lines = [
        "# " + full_meta["interpretation"],
        "",
        "150 cases / 510 calls; all five conditions.",
        "",
    ]
    for label, values in summaries.items():
        lines.extend(
            [
                f"## {label}",
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
            "| Contrast | Mean delta | Conditional CI95 | p | Secondary Holm p |",
            "|---|---:|---|---:|---|",
        ]
    )
    for values in comparisons.values():
        lines.append(
            f"| {values['contrast']} | {values['mean_difference']:.4f} "
            f"| {values['ci95']} | {values['p']:.4f} "
            f"| {values.get('holm_secondary_p', 'primary')} |"
        )
    lines.extend(["", *result["limitations"], "", "Mock results do not measure model capability."])
    (output / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output / "analysis.json"
