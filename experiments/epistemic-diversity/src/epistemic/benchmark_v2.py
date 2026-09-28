"""Versioned authored cases, independent expected answers, and balanced routing."""

import itertools
import random
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from app.core.models import Knowledge, Model
from epistemic.models import (
    DecisionRule,
    Family,
    Gold,
    GoldClaim,
    InferenceRule,
    PublicTask,
    TaskInstructions,
)
from epistemic.paths import ROOT, digest, read_json, write_json
from epistemic.reasoning import derive, observation, pair

VERSION = "2.0.0"
SEED = 20260928
PILOT_IDS = [
    "v2-synthesis-easy",
    "v2-diagnosis-medium",
    "v2-constraints-medium",
    "v2-contradiction-hard",
    "v2-missing-easy",
    "v2-causal-hard",
]
FAMILIES = [
    "synthesis",
    "diagnosis",
    "constraints",
    "contradiction",
    "missing",
    "causal",
    "decision",
    "failure",
    "planning",
    "ranking",
]


class CaseSpec(Model):
    id: str
    family: Family
    difficulty: Literal["easy", "medium", "hard"]
    structure: str
    depth: int
    prompt: str
    observations: dict[str, str]
    weak: dict[str, str] = Field(default_factory=dict)
    distractors: dict[str, str]
    rules: list[str]
    decisions: list[str]
    required: dict[str, list[str]]
    expected: str
    unknowns: list[str] = Field(default_factory=list)
    importance: dict[str, int] = Field(default_factory=dict)


def rule_parts(text: str) -> tuple[list[str], str]:
    left, right = text.split("->")
    return [part.strip() for part in left.split("&")], right.strip()


def compile_case(spec: CaseSpec) -> tuple[PublicTask, Gold]:
    """Gold expected decision/required witnesses are authored, not taken from mock output."""
    ids = {
        key: f"e_{digest([VERSION, spec.id, key])[:12]}"
        for key in spec.observations | spec.weak | spec.distractors
    }
    rules = [
        InferenceRule(
            premises=[pair(p) for p in rule_parts(rule)[0]], conclusion=pair(rule_parts(rule)[1])
        )
        for rule in spec.rules
    ]
    decisions = [
        DecisionRule(premises=[pair(p) for p in rule_parts(rule)[0]], choice=rule_parts(rule)[1])
        for rule in spec.decisions
    ]
    evidence = [
        Knowledge(
            id=ids[key],
            content=(
                f"Source record. Observation: {key} = {value}.\n"
                f"Source routing marker: CANARY_{digest([VERSION, spec.id, key, 'private'])[:16]}"
            ),
        )
        for key, value in (spec.observations | spec.weak | spec.distractors).items()
    ]
    random.Random(spec.id).shuffle(evidence)
    instructions = TaskInstructions(
        reporting_fields=list(spec.observations | spec.weak),
        inference_rules=rules,
        decision_rules=decisions,
    )
    public = PublicTask(
        id=spec.id,
        family=spec.family,
        template=spec.structure,
        question=spec.prompt,
        instructions=instructions,
        evidence=evidence,
        benchmark_version=VERSION,
        difficulty=spec.difficulty,
        dependency_depth=spec.depth,
        evidence_interaction_type=spec.structure,
    )
    claims = [
        c
        for d in evidence
        if (c := observation(d)) is not None and c.subject in instructions.reporting_fields
    ]
    proofs = derive(claims, rules)
    required = [
        GoldClaim(**pair(key).model_dump(), supporting_sets=[[ids[s] for s in support]])
        for key, support in spec.required.items()
    ]
    # Enumeration adds alternative minimal supports, but must contain the author's witness.
    for annotated in required:
        witness = frozenset(annotated.supporting_sets[0])
        if witness not in proofs.get(annotated.key(), set()):
            raise ValueError(f"Authored support disagrees with rules: {spec.id}/{annotated.key()}")
        annotated.supporting_sets = [
            sorted(s) for s in sorted(proofs[annotated.key()], key=lambda s: sorted(s))
        ]
    optional = [
        GoldClaim(
            **pair(key).model_dump(),
            supporting_sets=[sorted(s) for s in sorted(supports, key=lambda s: sorted(s))],
        )
        for key, supports in sorted(proofs.items())
        if pair(key).subject not in instructions.reporting_fields and key not in spec.required
    ]
    choices = [d for d in decisions if all(p.key() in proofs for p in d.premises)]
    if len(choices) != 1 or choices[0].choice != spec.expected:
        raise ValueError(f"Authored decision disagrees with public rules: {spec.id}")
    decision_supports = [
        sorted(frozenset().union(*supports))
        for supports in itertools.product(*(proofs[p.key()] for p in choices[0].premises))
    ]
    gold = Gold(
        task_id=spec.id,
        benchmark_version=VERSION,
        relevant_evidence_ids=[ids[k] for k in spec.observations],
        distractor_ids=[ids[k] for k in spec.distractors],
        weak_evidence_ids=[ids[k] for k in spec.weak],
        claims=[
            GoldClaim(subject=k, value=v, supporting_sets=[[ids[k]]])
            for k, v in spec.observations.items()
        ],
        optional_claims=[
            GoldClaim(subject=k, value=v, supporting_sets=[[ids[k]]]) for k, v in spec.weak.items()
        ],
        required_insights=required,
        optional_insights=optional,
        expected_conclusion=spec.expected,
        constraints=list(spec.observations),
        failure_factors=[],
        hidden_annotation=f"GOLD_ONLY_{digest([VERSION, spec.id])[:20]}",
        evidence_importance={ids[k]: spec.importance.get(k, 2) for k in spec.observations},
        decision_supporting_sets=decision_supports,
        allowed_uncertainty=spec.unknowns,
        required_unknowns=spec.unknowns,
        partition_note="Oracle relevance/importance strata; count difference at most one. "
        "Integer document weights may preclude identical importance totals. "
        "Assignment diagnostics record every remaining imbalance.",
    )
    return public, gold


def build_v2(root: Path = ROOT) -> None:
    folder = root / "benchmarks/v2"
    specs = [CaseSpec.model_validate(value) for value in read_json(folder / "specifications.json")]
    if len({s.id for s in specs}) != len(specs):
        raise ValueError("Duplicate task ID")
    entries = []
    for spec in specs:
        task, gold = compile_case(spec)
        write_json(folder / "public" / f"{task.id}.json", task.model_dump(mode="json"))
        write_json(folder / "gold" / f"{task.id}.json", gold.model_dump(mode="json"))
        entries.append(
            {
                "id": task.id,
                "family": task.family,
                "difficulty": task.difficulty,
                "structure": spec.structure,
                "dependency_depth": task.dependency_depth,
            }
        )
    write_json(
        folder / "manifest.json",
        {
            "benchmark_version": VERSION,
            "tasks": entries,
            "pilot": PILOT_IDS,
            "full": [s.id for s in specs],
            "main": [],
            "pilot_conditions": ["C2", "C3"],
            "seed": SEED,
        },
    )


def partition_stats(gold: Gold, groups: dict[str, list[str]]) -> dict[str, Any]:
    counts = {
        worker: {
            "relevant": len(set(ids) & set(gold.relevant_evidence_ids)),
            "weak": len(set(ids) & set(gold.weak_evidence_ids)),
            "distractors": len(set(ids) & set(gold.distractor_ids)),
            "importance": sum(gold.evidence_importance.get(eid, 0) for eid in ids),
        }
        for worker, ids in groups.items()
    }
    maximum_share = max(
        (
            len(set(ids) & set(support)) / len(support)
            for ids in groups.values()
            for support in gold.decision_supporting_sets
        ),
        default=0.0,
    )
    return {
        "workers": counts,
        "max_decision_support_share": maximum_share,
        "importance_range": max(c["importance"] for c in counts.values())
        - min(c["importance"] for c in counts.values()),
        "note": gold.partition_note,
    }


def balanced_partition(task: PublicTask, gold: Gold, seed: int) -> dict[str, list[str]]:
    rng = random.Random(digest([task.id, seed, VERSION, "partition"]))
    best: dict[str, list[str]] = {}
    best_score = (float("inf"), float("inf"))
    # Bounded search over balanced assignments, not outcome-dependent routing.
    for _ in range(128):
        groups: dict[str, list[str]] = {f"worker_{i}": [] for i in range(3)}
        for stratum in (gold.relevant_evidence_ids, gold.weak_evidence_ids, gold.distractor_ids):
            items = sorted(stratum)
            rng.shuffle(items)
            offset = rng.randrange(3)
            for i, item in enumerate(items):
                groups[f"worker_{(i + offset) % 3}"].append(item)
        weights = [
            sum(gold.evidence_importance.get(eid, 0) for eid in ids) for ids in groups.values()
        ]
        share = max(
            len(set(ids) & set(support)) / len(support)
            for ids in groups.values()
            for support in gold.decision_supporting_sets
        )
        score = (max(0.0, share - 2 / 3), float(max(weights) - min(weights)))
        if score < best_score:
            best, best_score = groups, score
    if not best or best_score[0] > 0:
        raise ValueError(f"No acceptable non-concentrated partition for {task.id}")
    for items in best.values():
        rng.shuffle(items)
    return best
