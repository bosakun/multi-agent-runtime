"""Pre-specified paired inference; repetitions are not independent samples."""

import csv
import math
import random
import statistics
from collections import defaultdict
from itertools import product
from pathlib import Path
from typing import Any

from epistemic.paths import digest, read_json, write_json
from epistemic.review import human_review

COMPARISONS = [
    ("P1", "C3", "C2"),
    ("P2", "C2", "C1"),
    ("P3", "C3", "C1"),
    ("P4", "C4", "C3"),
    ("P5", "C3", "C0"),
]
ENDPOINTS = ["gold_claim_coverage", "worker_evidence_coverage"]


def quantile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lo = math.floor(position)
    hi = math.ceil(position)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (position - lo)


def describe(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0, "mean": None, "median": None, "sd": None, "iqr": None}
    return {
        "n": len(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "sd": statistics.stdev(values) if len(values) > 1 else None,
        "iqr": quantile(values, 0.75) - quantile(values, 0.25),
    }


def paired_inference(differences: list[float], seed: int = 20260927) -> dict[str, Any]:
    n = len(differences)
    if not n:
        return {"n_tasks": 0, "mean_difference": None, "ci95": None, "dz": None, "p": None}
    observed = statistics.mean(differences)
    rng = random.Random(seed)
    draws = [statistics.mean(rng.choices(differences, k=n)) for _ in range(5000)]
    if n <= 16:
        null = (
            sum(d * s for d, s in zip(differences, signs, strict=True)) / n
            for signs in product((-1, 1), repeat=n)
        )
        p = sum(abs(value) >= abs(observed) - 1e-12 for value in null) / (2**n)
    else:
        hits = sum(
            abs(sum(d * rng.choice((-1, 1)) for d in differences) / n) >= abs(observed) - 1e-12
            for _ in range(20000)
        )
        p = (hits + 1) / 20001
    sd = statistics.stdev(differences) if n > 1 else 0
    return {
        "n_tasks": n,
        "mean_difference": observed,
        "ci95": [quantile(draws, 0.025), quantile(draws, 0.975)] if n > 1 else None,
        "dz": observed / sd if sd else None,
        "p": p,
        "task_differences": differences,
    }


def holm(values: list[float | None]) -> list[float | None]:
    result: list[float | None] = [None] * len(values)
    ordered = sorted((p, i) for i, p in enumerate(values) if p is not None)
    maximum = 0.0
    for rank, (p, index) in enumerate(ordered):
        maximum = max(maximum, min(1.0, p * (len(ordered) - rank)))
        result[index] = maximum
    return result


def mcnemar(pairs: list[tuple[int, int]]) -> dict[str, Any]:
    if not pairs:
        return {"n_tasks": 0, "wins": 0, "losses": 0, "p": None}
    wins = sum(a == 1 and b == 0 for a, b in pairs)
    losses = sum(a == 0 and b == 1 for a, b in pairs)
    discordant = wins + losses
    p = (
        min(
            1.0,
            2
            * sum(math.comb(discordant, k) for k in range(min(wins, losses) + 1))
            / (2**discordant),
        )
        if discordant
        else 1.0
    )
    return {"n_tasks": len(pairs), "wins": wins, "losses": losses, "p": p}


def aggregate(
    records: list[dict[str, Any]], expected_conditions: list[str] | None = None
) -> dict[str, Any]:
    expected_conditions = expected_conditions or ["C0", "C1", "C2", "C3", "C4"]
    for field in ("benchmark_version", "metrics_version", "protocol_fingerprint", "model_settings"):
        if len({digest(r.get(field)) for r in records}) > 1:
            raise ValueError(f"Do not pool different {field} cohorts")
    v2 = bool(records and records[0].get("benchmark_version") == "2.0.0")
    indexed: dict[tuple[str, int, str], dict[str, Any]] = {}
    for record in records:
        key = (record["task_id"], record["repetition"], record["condition"])
        if key in indexed:
            raise ValueError("Duplicate task/repetition/condition record")
        indexed[key] = record
    metric_names = sorted({name for r in records for name in r["metrics"]})
    summaries: dict[str, Any] = {}
    for condition in sorted({r["condition"] for r in records}):
        summaries[condition] = {}
        for metric in metric_names:
            by_task: dict[str, list[float]] = defaultdict(list)
            for r in records:
                if r["condition"] == condition and r["metrics"].get(metric) is not None:
                    by_task[r["task_id"]].append(float(r["metrics"][metric]))
            summaries[condition][metric] = describe([statistics.mean(v) for v in by_task.values()])
    primary: list[dict[str, Any]] = []
    binary: list[dict[str, Any]] = []
    for label, a, b in COMPARISONS:
        if a not in expected_conditions or b not in expected_conditions:
            continue
        for metric in ENDPOINTS:
            by_task_diff: dict[str, list[float]] = defaultdict(list)
            for (task, repetition, condition), record in indexed.items():
                other = indexed.get((task, repetition, b))
                if condition == a and other is not None:
                    by_task_diff[task].append(
                        float(record["metrics"][metric]) - float(other["metrics"][metric])
                    )
            paired_values = {
                task: statistics.mean(values) for task, values in sorted(by_task_diff.items())
            }
            clusters: dict[str, list[float]] = defaultdict(list)
            for task, value in paired_values.items():
                cluster = next(r["family"] for r in records if r["task_id"] == task) if v2 else task
                clusters[cluster].append(value)
            primary.append(
                {
                    "comparison": label,
                    "a": a,
                    "b": b,
                    "endpoint": metric,
                    **paired_inference([statistics.mean(v) for _, v in sorted(clusters.items())]),
                    "resampling_unit": "family" if v2 else "task",
                    "n_units": len(clusters),
                    "n_tasks": len(paired_values),
                    "n_pairs_tasks": len(paired_values),
                    "task_level_differences": paired_values,
                }
            )
        pairs = [
            (
                int(r["metrics"]["task_success"]),
                int(indexed[(task, 0, b)]["metrics"]["task_success"]),
            )
            for (task, repetition, condition), r in indexed.items()
            if repetition == 0 and condition == a and (task, 0, b) in indexed
        ]
        result = {"comparison": label, "a": a, "b": b, **mcnemar(pairs)}
        if v2 and len({r["family"] for r in records}) < len({r["task_id"] for r in records}):
            result["p"] = None
            result["note"] = (
                "Discordance counts only: repeated cases within family violate "
                "independent-pair McNemar assumption"
            )
        binary.append(result)
    for family in (primary, binary):
        for item, adjusted in zip(family, holm([p["p"] for p in family]), strict=True):
            item["p_holm"] = adjusted
    incomplete = [
        {
            "task": task,
            "repetition": repetition,
            "missing": [c for c in expected_conditions if (task, repetition, c) not in indexed],
        }
        for task, repetition in sorted({(t, r) for t, r, _ in indexed})
        if any((task, repetition, c) not in indexed for c in expected_conditions)
    ]
    failures = []
    for (task, repetition, condition), role in indexed.items():
        epistemic = indexed.get((task, repetition, "C3"))
        if (
            condition == "C2"
            and epistemic
            and role["metrics"]["task_success"] != epistemic["metrics"]["task_success"]
        ):
            failures.append(
                {
                    "task": task,
                    "repetition": repetition,
                    "winner": "C2" if role["metrics"]["task_success"] else "C3",
                    "C2": role,
                    "C3": epistemic,
                }
            )
    return {
        "runs": len(records),
        "tasks": len({r["task_id"] for r in records}),
        "summaries": summaries,
        "primary": primary,
        "binary_secondary": binary,
        "incomplete_blocks": incomplete,
        "failure_cases": failures,
        "failure_case_note": "Observed discordant pairs attached."
        if failures
        else "No C2-success/C3-failure or C3-success/C2-failure pair was observed.",
    }


def analyze(input_path: Path, output_dir: Path) -> Path:
    data = read_json(input_path)
    records = data["records"]
    if not records:
        raise ValueError("No executed records to analyze")
    output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "metadata": data["metadata"],
        "input_sha256": digest(data),
        **aggregate(records, data["metadata"].get("plan", {}).get("conditions")),
    }
    executed = {(r["task_id"], r["repetition"], r["condition"]) for r in records}
    report["planned_but_unexecuted"] = [
        [task, rep, condition]
        for task, rep in data["metadata"].get("plan", {}).get("blocks", [])
        for condition in data["metadata"]["plan"]["conditions"]
        if (task, rep, condition) not in executed
    ]
    write_json(output_dir / "analysis.json", report)
    # Committed compact records are sufficient to regenerate every reported statistic/figure.
    write_json(output_dir / "records.json", data)
    human_review(data, output_dir / "pilot-human-review.md")
    fields = [
        "task_id",
        "condition",
        "repetition",
        "seed",
        "status",
        *sorted(records[0]["metrics"]),
    ]
    with (output_dir / "metrics.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow({**{key: record[key] for key in fields[:5]}, **record["metrics"]})
    lines = [
        f"# {data['metadata']['interpretation']}",
        "",
        f"Executed {report['runs']} runs across {report['tasks']} tasks.",
        "",
        "| Condition | Success | Claim coverage | Evidence coverage | Unique evidence "
        "| Redundancy |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for condition, summary in report["summaries"].items():
        values = [
            summary[m]["mean"]
            for m in (
                "task_success",
                "gold_claim_coverage",
                "worker_evidence_coverage",
                "evidence_unique",
                "evidence_redundancy",
            )
        ]
        lines.append(
            f"| {condition} | "
            + " | ".join("N/A" if v is None else f"{v:.3f}" for v in values)
            + " |"
        )
    lines.extend(
        [
            "",
            report["failure_case_note"],
            "",
            "Paired intervals/tests are in analysis.json. Mock intervals describe a deterministic",
            "interpreter, not an estimate of LLM effects. "
            "Zero-width intervals are not empirical certainty.",
        ]
    )
    (output_dir / "summary.md").write_text("\n".join(lines) + "\n")
    return output_dir / "analysis.json"
