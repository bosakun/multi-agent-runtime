"""Generate and validate controlled public tasks and separately stored gold."""

import random
from typing import Any

from app.core.models import Knowledge
from epistemic.models import (
    DecisionRule,
    Gold,
    GoldClaim,
    InferenceRule,
    Pair,
    PublicTask,
    TaskInstructions,
)
from epistemic.paths import ROOT, digest, read_json, write_json


def build_benchmark() -> None:
    """Materialize all 24 cases from authored specifications, without model calls."""
    specs: list[dict[str, Any]] = read_json(ROOT / "benchmarks/specifications.json")
    manifest: list[dict[str, str]] = []
    counters = {"distributed_evidence": 0, "multi_perspective": 0}
    for spec in specs:
        family = spec["family"]
        for variant in range(4):
            counters[family] += 1
            task_id = ("a" if family == "distributed_evidence" else "b") + f"{counters[family]:02}"
            document_ids = [f"e_{digest([task_id, i])[:10]}" for i in range(9)]
            bits = [variant // 2, variant % 2]
            facts = [
                Pair(subject=subject, value=spec["values"][i][0 if bits[i // 3] else 1])
                for i, subject in enumerate(spec["subjects"])
            ]
            rules = [
                InferenceRule(
                    premises=[
                        Pair(subject=spec["subjects"][i], value=spec["values"][i][0 if bit else 1])
                        for i in range(group * 3, group * 3 + 3)
                    ],
                    conclusion=Pair(subject=spec["insights"][group], value="yes" if bit else "no"),
                )
                for group in range(2)
                for bit in range(2)
            ]
            decisions = [
                DecisionRule(
                    premises=[
                        Pair(subject=spec["insights"][i], value="yes" if bit else "no")
                        for i, bit in enumerate([choice // 2, choice % 2])
                    ],
                    choice=spec["choices"][choice],
                )
                for choice in range(4)
            ]
            evidence = [
                Knowledge(
                    id=document_ids[i],
                    content=(
                        f"Case record {i + 1}. Observation: {fact.subject} = {fact.value}. "
                        "This report concerns the current case.\n"
                        f"Source routing marker: CANARY_{digest([task_id, i, 'private'])[:16]}"
                    ),
                )
                for i, fact in enumerate(facts)
            ]
            evidence.extend(
                Knowledge(
                    id=document_ids[6 + i],
                    content=(
                        f"Unrelated archival note. Observation: archival_{i} = unchanged. "
                        "This note refers to a different case and has no bearing "
                        "on the current decision.\n"
                        f"Source routing marker: CANARY_{digest([task_id, 6 + i, 'private'])[:16]}"
                    ),
                )
                for i in range(3)
            )
            random.Random(task_id).shuffle(evidence)
            public = PublicTask(
                id=task_id,
                family=family,
                template=spec["template"],
                question=spec["context"],
                instructions=TaskInstructions(
                    reporting_fields=spec["subjects"],
                    inference_rules=rules,
                    decision_rules=decisions,
                ),
                evidence=evidence,
            )
            gold = Gold(
                task_id=task_id,
                relevant_evidence_ids=document_ids[:6],
                distractor_ids=document_ids[6:],
                claims=[
                    GoldClaim(**fact.model_dump(), supporting_sets=[[document_ids[i]]])
                    for i, fact in enumerate(facts)
                ],
                required_insights=[
                    GoldClaim(
                        subject=spec["insights"][i],
                        value="yes" if bit else "no",
                        supporting_sets=[document_ids[i * 3 : i * 3 + 3]],
                    )
                    for i, bit in enumerate(bits)
                ],
                expected_conclusion=spec["choices"][variant],
                constraints=spec["subjects"],
                failure_factors=[facts[i].subject for i in range(6) if not bits[i // 3]],
                hidden_annotation=f"GOLD_ONLY_{digest([task_id, 'gold'])[:20]}",
            )
            folder = ROOT / "benchmarks" / family
            write_json(
                folder / "public" / f"{task_id}.json",
                public.model_dump(
                    mode="json",
                    exclude={
                        "benchmark_version",
                        "difficulty",
                        "dependency_depth",
                        "evidence_interaction_type",
                    },
                ),
            )
            write_json(
                folder / "gold" / f"{task_id}.json",
                gold.model_dump(
                    mode="json",
                    exclude={
                        "benchmark_version",
                        "optional_claims",
                        "weak_evidence_ids",
                        "evidence_importance",
                        "decision_supporting_sets",
                        "allowed_uncertainty",
                        "required_unknowns",
                        "partition_note",
                    },
                ),
            )
            manifest.append({"id": task_id, "family": family, "template": spec["template"]})
    write_json(
        ROOT / "benchmarks/manifest.json",
        {
            "version": "v1",
            "tasks": manifest,
            "pilot": ["a01", "b01"],
            "main": ["a02", "a03", "b02", "b03"],
            "full": [entry["id"] for entry in manifest],
        },
    )


def load_task(task_id: str) -> tuple[PublicTask, Gold]:
    if task_id.startswith("v2-"):
        folder = ROOT / "benchmarks/v2"
        public = PublicTask.model_validate(read_json(folder / "public" / f"{task_id}.json"))
        gold = Gold.model_validate(read_json(folder / "gold" / f"{task_id}.json"))
        return public, gold
    family = "distributed_evidence" if task_id.startswith("a") else "multi_perspective"
    folder = ROOT / "benchmarks" / family
    public = PublicTask.model_validate(read_json(folder / "public" / f"{task_id}.json"))
    gold = Gold.model_validate(read_json(folder / "gold" / f"{task_id}.json"))
    return public, gold


def partition(task: PublicTask, gold: Gold, seed: int) -> dict[str, list[str]]:
    """Oracle-balanced assignment; only the resulting IDs enter ContextAccess."""
    if task.benchmark_version == "2.0.0":
        from epistemic.benchmark_v2 import balanced_partition

        return balanced_partition(task, gold, seed)
    rng = random.Random(digest([task.id, seed, "partition"]))
    relevant = sorted(gold.relevant_evidence_ids)
    distractors = sorted(gold.distractor_ids)
    rng.shuffle(relevant)
    rng.shuffle(distractors)
    result = {f"worker_{i}": relevant[i::3] + [distractors[i]] for i in range(3)}
    for items in result.values():
        rng.shuffle(items)
    return result


def selected_tasks(subset: str, version: str = "1.0.0") -> list[str]:
    if version not in {"1.0.0", "2.0.0"}:
        raise ValueError("Unknown benchmark version")
    manifest = read_json(
        ROOT / ("benchmarks/v2/manifest.json" if version == "2.0.0" else "benchmarks/manifest.json")
    )
    return list(manifest[subset])
