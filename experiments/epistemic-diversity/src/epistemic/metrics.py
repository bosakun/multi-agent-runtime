"""Canonical evidence-level scoring; no LLM judge, embeddings or lexical proxies."""

import json
import re
import statistics
from collections import Counter, defaultdict
from itertools import combinations
from typing import Any

from app.core.models import Run, Status, Uncertainty
from app.llm.provider import ModelRequest
from epistemic.models import CallRecord, Claim, Gold, GoldClaim, PublicTask, WorkerOutput

Metric = float | int | None


def valid_claim(claim: Claim, annotations: list[GoldClaim]) -> bool:
    """Require exact canonical value and complete, non-extraneous evidence support."""
    cited = set(claim.evidence_ids)
    return any(
        claim.key() == gold.key() and any(cited == set(s) for s in gold.supporting_sets)
        for gold in annotations
    )


def valid_items(output: WorkerOutput, gold: Gold) -> list[Claim]:
    return [
        c
        for c in output.claims + output.insights
        if valid_claim(
            c, gold.claims + gold.optional_claims + gold.required_insights + gold.optional_insights
        )
    ]


def diversity(sets: list[set[str]]) -> dict[str, float | None]:
    if len(sets) < 2:
        return {"unique": None, "redundancy": None, "jaccard": None}
    counts = Counter(item for items in sets for item in items)
    total = sum(counts.values())
    overlaps = [len(a & b) / len(a | b) for a, b in combinations(sets, 2) if a | b]
    return {
        "unique": sum(count == 1 for count in counts.values()) / len(counts) if counts else 0,
        "redundancy": (total - len(counts)) / total if total else 0,
        "jaccard": statistics.mean(overlaps) if overlaps else None,
    }


def contradictions(claims: list[Claim]) -> int:
    values: dict[str, set[str]] = defaultdict(set)
    for claim in claims:
        values[claim.subject.strip().lower()].add(claim.value.strip().lower())
    return sum(len(items) > 1 for items in values.values())


def collective_gain(sets: list[set[str]], universe: set[str]) -> float:
    """Useful union coverage minus the strongest observed individual coverage."""
    if not universe or not sets:
        return 0.0
    return (len(set().union(*sets) & universe) - max(len(s & universe) for s in sets)) / len(
        universe
    )


def marginal_support(
    worker_evidence: list[set[str]],
    final_keys: set[str],
    gold_claims: list[GoldClaim],
) -> list[dict[str, float]]:
    """Fixed-output provenance counterfactual, NOT an LLM re-generation ablation."""
    denominator = len(gold_claims)

    def coverage(evidence: set[str]) -> float:
        return (
            sum(
                c.key() in final_keys and any(set(s) <= evidence for s in c.supporting_sets)
                for c in gold_claims
            )
            / denominator
            if denominator
            else 0.0
        )

    baseline = coverage(set().union(*worker_evidence))
    return [
        {
            "supported_final_coverage_without": coverage(
                set().union(*(items for j, items in enumerate(worker_evidence) if j != i))
            ),
            "drop": baseline
            - coverage(set().union(*(items for j, items in enumerate(worker_evidence) if j != i))),
        }
        for i in range(len(worker_evidence))
    ]


def audit(
    task: PublicTask,
    gold: Gold,
    calls: list[CallRecord],
    run: Run,
) -> dict[str, int]:
    """Audit observed boundaries against configured ACLs, not against leaked context."""
    counts = {
        "context_leaks": 0,
        "result_leaks": 0,
        "gold_leaks": 0,
        "raw_exposure_outside_partition": 0,
    }
    markers = {doc.id: re.findall(r"CANARY_[a-f0-9]+", doc.content) for doc in task.evidence}
    all_ids = set(markers)
    for call in calls:
        request = ModelRequest.model_validate(call.request)
        agent = run.agents[call.agent_id]
        allowed_raw = set(agent.context.knowledge_ids)
        authorized_artifacts = [
            a
            for a in run.state.artifacts
            if a.producer in agent.context.artifact_producers and agent.id in a.readers
        ]
        allowed_ids = allowed_raw | {eid for a in authorized_artifacts for eid in a.evidence_ids}
        released_text = json.dumps([a.model_dump(mode="json") for a in authorized_artifacts])
        for kind, value in (("context", call.request), ("result", call.response)):
            text = json.dumps(value, sort_keys=True)
            counts[f"{kind}_leaks"] += sum(eid in text for eid in all_ids - allowed_ids)
            counts[f"{kind}_leaks"] += sum(
                marker in text
                for eid, items in markers.items()
                if eid not in allowed_raw
                for marker in items
                if marker not in released_text
            )
            counts["gold_leaks"] += int(
                gold.hidden_annotation in text
                or any(
                    f'"{key}"' in text
                    for key in (
                        "hidden_annotation",
                        "supporting_sets",
                        "expected_conclusion",
                        "relevant_evidence_ids",
                    )
                )
            )
        # Keep validation separate: an unexpected document is a boundary breach even
        # if no known canary was present (e.g. novel external document).
        counts["context_leaks"] += len(
            {d.id for d in request.context.knowledge} - allowed_raw - all_ids
        )
    return counts


def evaluate(run: Run, gold: Gold) -> tuple[dict[str, Metric], dict[str, Any]]:
    workers = [a for a in run.state.artifacts if a.producer.startswith("worker_")]
    outputs = [
        WorkerOutput.model_validate({k: a.payload[k] for k in WorkerOutput.model_fields})
        for a in workers
    ]
    # Missing/failed workers remain represented as empty sets.
    by_worker = {a.producer: o for a, o in zip(workers, outputs, strict=True)}
    worker_outputs = [
        by_worker.get(key, WorkerOutput(claims=[], insights=[], uncertainty=Uncertainty()))
        for key in run.agents
        if key.startswith("worker_")
    ]
    valid = [valid_items(output, gold) for output in worker_outputs]
    raw_evidence_sets = [{eid for c in items for eid in c.evidence_ids} for items in valid]
    relevant = set(gold.relevant_evidence_ids)
    evidence_sets = [ids & relevant for ids in raw_evidence_sets]
    fact_keys = {c.key() for c in gold.claims}
    insight_keys = {c.key() for c in gold.required_insights}
    claim_sets = [{c.key() for c in items} & fact_keys for items in valid]
    insight_sets = [{c.key() for c in items} & insight_keys for items in valid]
    final = next((a for a in run.state.artifacts if a.id in run.state.final_artifact_ids), None)
    final_output = (
        WorkerOutput.model_validate({k: final.payload[k] for k in WorkerOutput.model_fields})
        if final
        else WorkerOutput(claims=[], insights=[], uncertainty=Uncertainty())
    )
    final_valid = valid_items(final_output, gold)
    final_keys = {c.key() for c in final_valid}
    final_evidence = {eid for c in final_valid for eid in c.evidence_ids}
    relevant = set(gold.relevant_evidence_ids)
    unsupported = len(final_output.claims + final_output.insights) - len(final_valid)
    final_conflicts = contradictions(final_output.claims + final_output.insights)
    success = (
        run.status == Status.SUCCEEDED
        and final is not None
        and final.payload.get("conclusion") == gold.expected_conclusion
        and all(c.key() in final_keys for c in gold.claims + gold.required_insights)
        and not unsupported
        and not final_conflicts
        and set(gold.required_unknowns) <= set(final_output.uncertainty.unknowns)
        and (
            gold.benchmark_version == "1.0.0"
            or set(final_output.uncertainty.unknowns) <= set(gold.allowed_uncertainty)
        )
    )
    score: dict[str, Metric] = {
        "task_success": int(success),
        "gold_claim_coverage": sum(c.key() in final_keys for c in gold.claims) / len(gold.claims),
        "required_insight_coverage": sum(c.key() in final_keys for c in gold.required_insights)
        / len(gold.required_insights),
        "worker_evidence_coverage": len(set().union(*evidence_sets) & relevant) / len(relevant),
        "final_evidence_coverage": len(final_evidence & relevant) / len(relevant),
        "worker_distinct_insights": len(set().union(*insight_sets)),
        "worker_contradictions": contradictions(
            [c for o in worker_outputs for c in o.claims + o.insights]
        ),
        "final_contradictions": final_conflicts,
        "unsupported_claims": unsupported,
        "worker_unsupported_claims": sum(
            len(o.claims + o.insights) - len(v) for o, v in zip(worker_outputs, valid, strict=True)
        ),
        "agent_failures": sum(a.status == Status.FAILED for a in run.state.agent_runs),
        "collective_evidence_coverage_gain": collective_gain(evidence_sets, relevant),
        "collective_claim_coverage_gain": collective_gain(claim_sets, fact_keys),
        "collective_insight_coverage_gain": collective_gain(insight_sets, insight_keys),
    }
    marginals = marginal_support(raw_evidence_sets, final_keys, gold.claims)
    insight_marginals = marginal_support(raw_evidence_sets, final_keys, gold.required_insights)
    score["marginal_final_support_loss_mean"] = statistics.mean(m["drop"] for m in marginals)
    score["marginal_final_support_loss_max"] = max(m["drop"] for m in marginals)
    for prefix, sets in (
        ("evidence", evidence_sets),
        ("claim", claim_sets),
        ("insight", insight_sets),
    ):
        score.update({f"{prefix}_{key}": value for key, value in diversity(sets).items()})
    if run.status != Status.SUCCEEDED:
        for key in (
            "gold_claim_coverage",
            "required_insight_coverage",
            "final_evidence_coverage",
        ):
            score[key] = 0
    diagnostics = {
        "missing_claims": sorted({c.key() for c in gold.claims} - final_keys),
        "missing_insights": sorted({c.key() for c in gold.required_insights} - final_keys),
        "worker_valid_keys": [sorted(items) for items in claim_sets],
        "worker_evidence": [sorted(items) for items in evidence_sets],
        "worker_required_insights": [sorted(items) for items in insight_sets],
        "marginal_final_claim_support": marginals,
        "marginal_final_insight_support": insight_marginals,
        "marginal_method": "fixed final-output provenance support loss; no re-generation",
        "expected_conclusion": gold.expected_conclusion,
        "actual_conclusion": final.payload.get("conclusion") if final else None,
    }
    return score, diagnostics
