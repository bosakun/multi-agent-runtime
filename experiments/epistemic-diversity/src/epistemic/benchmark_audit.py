"""Static quality checks independent of model outputs; findings are not suppressed."""

import itertools
import re
from collections import Counter
from pathlib import Path
from typing import Any

from epistemic.benchmark import load_task, partition, selected_tasks
from epistemic.benchmark_v2 import FAMILIES, PILOT_IDS, SEED, VERSION, partition_stats
from epistemic.conditions import build_condition, configurations
from epistemic.models import ModelSettings, PublicTask, TaskInstructions
from epistemic.paths import ROOT, digest, write_json
from epistemic.reasoning import observation


def consequences(task: PublicTask, ids: set[str]) -> tuple[set[str], set[str]]:
    """Independent Boolean closure (not mock's provenance engine)."""
    facts = {
        c.key()
        for d in task.evidence
        if d.id in ids
        and (c := observation(d)) is not None
        and c.subject in task.instructions.reporting_fields
    }
    while True:
        extra = {
            r.conclusion.key()
            for r in task.instructions.inference_rules
            if all(p.key() in facts for p in r.premises)
        }
        if extra <= facts:
            break
        facts |= extra
    choices = {
        r.choice
        for r in task.instructions.decision_rules
        if all(p.key() in facts for p in r.premises)
    }
    return facts, choices


def ngrams(text: str) -> set[tuple[str, ...]]:
    tokens = re.findall(r"[a-z]+", re.sub(r"CANARY_\w+|e_[a-f0-9]+", "", text).lower())
    return set(zip(tokens, tokens[1:], tokens[2:], strict=False))


def dependency_depth(task: PublicTask) -> int:
    depths = {c.key(): 0 for d in task.evidence if (c := observation(d)) is not None}
    for _ in range(len(task.instructions.inference_rules) + 1):
        for rule in task.instructions.inference_rules:
            if all(p.key() in depths for p in rule.premises):
                depth = 1 + max(depths[p.key()] for p in rule.premises)
                depths[rule.conclusion.key()] = min(depths.get(rule.conclusion.key(), depth), depth)
    return max(depths.values())


def quality_audit() -> dict[str, Any]:
    tasks = [load_task(task_id) for task_id in selected_tasks("full", VERSION)]
    errors: list[str] = []
    entries = []
    text_sets: dict[str, set[tuple[str, ...]]] = {}
    exact_hashes: dict[str, str] = {}
    structural: dict[str, list[str]] = {}
    candidate_positions: dict[str, int] = {}
    for task, gold in tasks:
        all_ids = {d.id for d in task.evidence}
        if len(all_ids) != len(task.evidence):
            errors.append(f"duplicate_document_id:{task.id}")
        if gold.hidden_annotation in task.model_dump_json() or any(
            f'"{key}"' in task.model_dump_json()
            for key in (
                "supporting_sets",
                "expected_conclusion",
                "required_unknowns",
                "evidence_importance",
            )
        ):
            errors.append(f"gold_leak:{task.id}")
        facts, choices = consequences(task, all_ids)
        if dependency_depth(task) != task.dependency_depth:
            errors.append(f"incorrect_dependency_depth:{task.id}")
        if choices != {gold.expected_conclusion} or not all(
            c.key() in facts for c in gold.required_insights
        ):
            errors.append(f"impossible_or_ambiguous:{task.id}")
        if consequences(task, set())[1]:
            errors.append(f"instruction_only_solution:{task.id}")
        if any(consequences(task, {eid})[1] for eid in all_ids):
            errors.append(f"one_document_solution:{task.id}")
        minimal = next(
            (
                size
                for size in range(1, len(all_ids) + 1)
                if any(
                    gold.expected_conclusion in consequences(task, set(ids))[1]
                    for ids in itertools.combinations(sorted(all_ids), size)
                )
            ),
            0,
        )
        if minimal < 3:
            errors.append(f"trivial_decision_support:{task.id}")
        if len({r.choice for r in task.instructions.decision_rules}) < 2:
            errors.append(f"single_candidate_answer:{task.id}")
        inputs = build_condition(task, configurations()[0], {}, SEED, ModelSettings())[2].inputs
        choices_in_order = [
            rule.choice for rule in TaskInstructions.model_validate(inputs).decision_rules
        ]
        candidate_positions[task.id] = choices_in_order.index(gold.expected_conclusion)
        # Source-qualified reports do not share a resolved-variable key.
        subjects = [key.split("=", 1)[0] for key in facts]
        if len(subjects) != len(set(subjects)):
            errors.append(f"canonical_subject_conflict:{task.id}")
        assignments = []
        for seed in [SEED, SEED + 1, 0, 1, 42, 1729]:
            groups = partition(task, gold, seed)
            stats = partition_stats(gold, groups)
            counts = stats["workers"]
            assert isinstance(counts, dict)
            for category in ["relevant", "weak", "distractors"]:
                values = [v[category] for v in counts.values()]
                if max(values) - min(values) > 1:
                    errors.append(f"unbalanced_{category}:{task.id}:{seed}")
            if float(stats["max_decision_support_share"]) > 2 / 3 + 1e-9:
                errors.append(f"concentrated_decision:{task.id}:{seed}")
            if int(stats["importance_range"]) > 3:
                errors.append(f"importance_imbalance:{task.id}:{seed}")
            if set().union(*map(set, groups.values())) != all_ids or sum(
                map(len, groups.values())
            ) != len(all_ids):
                errors.append(f"partition_not_disjoint_exhaustive:{task.id}:{seed}")
            assignments.append({"seed": seed, **stats})
        source_text = (
            task.question
            + " "
            + " ".join(
                f"{c.subject} {c.value}" for d in task.evidence if (c := observation(d)) is not None
            )
        )
        key = digest(" ".join(re.findall(r"[a-z]+", source_text.lower())))
        if key in exact_hashes:
            errors.append(f"duplicate_task:{task.id}:{exact_hashes[key]}")
        exact_hashes[key] = task.id
        text_sets[task.id] = ngrams(source_text)
        shape = digest(
            [
                sorted(len(r.premises) for r in task.instructions.inference_rules),
                sorted(len(r.premises) for r in task.instructions.decision_rules),
                sorted(len(s) for s in gold.decision_supporting_sets),
                len(task.instructions.reporting_fields),
                task.dependency_depth,
            ]
        )[:12]
        structural.setdefault(shape, []).append(task.id)
        entries.append(
            {
                "id": task.id,
                "family": task.family,
                "difficulty": task.difficulty,
                "minimum_decision_documents": minimal,
                "source_count": len(all_ids),
                "structure": task.evidence_interaction_type,
                "structural_signature": shape,
                "partitions": assignments,
            }
        )
    similarities: list[dict[str, Any]] = []
    for (a, aset), (b, bset) in itertools.combinations(text_sets.items(), 2):
        score = len(aset & bset) / len(aset | bset) if aset | bset else 1.0
        similarities.append({"a": a, "b": b, "trigram_jaccard": score})
        if score >= 0.65:
            errors.append(f"near_duplicate_requires_review:{a}:{b}")
    families = Counter(t.family for t, _ in tasks)
    if set(families) != set(FAMILIES) or set(families.values()) != {3}:
        errors.append("family_imbalance")
    return {
        "benchmark_version": VERSION,
        "passed": not errors,
        "errors": errors,
        "tasks": len(tasks),
        "families": dict(families),
        "difficulty_counts": dict(Counter(t.difficulty for t, _ in tasks)),
        "entries": entries,
        "near_duplicate_threshold": 0.65,
        "top_text_similarities": sorted(
            similarities, key=lambda x: float(x["trigram_jaccard"]), reverse=True
        )[:10],
        "structural_signatures": len(structural),
        "shared_structural_signatures": [v for v in structural.values() if len(v) > 1],
        "runtime_candidate_positions": {
            "seed": SEED,
            "full": dict(Counter(candidate_positions.values())),
            "pilot": dict(Counter(candidate_positions[t] for t in PILOT_IDS)),
            "per_task": candidate_positions,
        },
        "review_note": "Lexical/degree signatures are screens, "
        "not a proof of semantic independence. "
        "Shared simple conjunction controls are retained; stronger cases differ in topology. "
        "Public prompts were manually reviewed to remove case-specific answer hints.",
    }


def write_audit(output: Path = ROOT / "docs/benchmark-audit.md") -> dict[str, Any]:
    report = quality_audit()
    write_json(ROOT / "benchmarks/v2/audit.json", report)
    lines = [
        "# Benchmark 2.0.0 audit (pre-model)",
        "",
        "Generated by `run.py audit`; no model results used.",
        "",
        f"Pass: {report['passed']}. Tasks: {report['tasks']}. Families: {len(report['families'])}.",
        f"Difficulty counts: {report['difficulty_counts']}.",
        "",
        "Checks: unique task/document IDs, gold fields/canaries, independent Boolean solvability,",
        "instruction-only/single-document shortcuts, minimum decision support >=3 documents,",
        "multiple candidate conclusions, normalized exact/near duplicates, subject conflicts,",
        "family balance and 180 seeded partition assignments. Stratum count ranges <=1;",
        "maximum decision support held by one worker <=2/3; importance range <=3 points.",
        "",
        "| Task | Difficulty | Minimum decision documents | Structural signature |",
        "|---|---|---:|---|",
    ]
    lines += [
        f"| {e['id']} | {e['difficulty']} | {e['minimum_decision_documents']} "
        f"| {e['structural_signature']} |"
        for e in report["entries"]
    ]
    lines += [
        "",
        f"Errors: {report['errors']}",
        "",
        f"Distinct coarse graph signatures: {report['structural_signatures']}.",
        f"Shared signatures: {report['shared_structural_signatures']}",
        "",
        "## Near-duplicate screen",
        "",
        "Top normalized word-trigram Jaccards (threshold 0.65):",
        "",
    ]
    lines += [
        f"- {r['a']} / {r['b']}: {r['trigram_jaccard']:.3f}"
        for r in report["top_text_similarities"]
    ]
    lines += [
        "",
        "## Manual review and remaining threats",
        "",
        report["review_note"],
        "",
        "Protocol 2.1 corrected an authoring-order confound: the canonical first candidate",
        "was always correct. Runtime now shuffles public criteria without consulting gold,",
        "identically across conditions for each task/seed. Zero-based runtime positions:",
        f"full {report['runtime_candidate_positions']['full']}; "
        f"pilot {report['runtime_candidate_positions']['pilot']}.",
        "This is not perfectly balanced; no task or seed was reselected to tune it.",
        "See protocol-2.1-amendment.md for preservation of the superseded freeze/results.",
        "",
        "Pre-freeze review removed answer-bearing wording from diagnosis, missing-information,",
        "contradiction, causal, failure and ranking prompts. An opening observation and its",
        "validation now use separate canonical fields to avoid a spurious contradiction.",
        "No outcome-based task selection was used. Integer weights/counts cannot always be equal;",
        "every task's Gold.partition_note and audit.json list the residual imbalance.",
        "Relevance and weights are oracle annotations used by host routing; "
        "this remains a confound.",
        "All tasks can be solved with full context; none requires isolation "
        "as a logical prerequisite.",
        "Single-agent full context may benefit on contradiction, planning and global-cause cases.",
        "Automatic checks cannot prove absence of semantic hints or human-level difficulty.",
        "Independent human benchmark review remains recommended before publication.",
    ]
    output.write_text("\n".join(lines) + "\n")
    return report
