"""Deterministic analysis of supplied human labels; never creates semantic labels."""

from collections import Counter
from dataclasses import dataclass
from statistics import mean

from review_v3.logic import (
    Outcome,
    conjunction,
    disjunction,
    path_outcomes,
    question_path_outcome,
    state_outcome,
)


@dataclass(frozen=True)
class Unit:
    question_id: str
    unit_id: str
    outcome: Outcome


def observed_state(record, field="state"):
    if record is None:
        return None
    if record.applicability is None:
        return None
    if record.applicability == "unclear":
        return "unclear"
    if record.applicability == "not_applicable":
        return "NA"
    return getattr(record, field)


def reference_eligibility(shared):
    state = observed_state(shared.s0)
    if state == "complete":
        return None
    if state in ("partial", "absent"):
        return Outcome.INELIGIBLE
    return Outcome.MISSING if state is None else Outcome.NA if state == "NA" else Outcome.UNCLEAR


def prerequisite(state, success):
    outcome = state_outcome(state, success)
    return Outcome.INELIGIBLE if outcome == Outcome.FAILURE else outcome


def fact_e2e(shared, received, sensitivity=False):
    eligible = reference_eligibility(shared)
    if eligible is not None:
        return eligible
    transition = shared.s3.publication_transition_type
    if transition is None:
        return Outcome.MISSING
    if transition == "unknown":
        return Outcome.NON_IDENTIFIABLE
    states = [
        state_outcome(observed_state(shared.s1), {"complete"}, {"partial"}, sensitivity),
        state_outcome(observed_state(shared.s2), {"correct"}, {"partial"}, sensitivity),
    ]
    if transition == "separate_records":
        states.append(
            state_outcome(observed_state(shared.s3), {"retained"}, {"partial_loss"}, sensitivity)
        )
    # alias bypasses S3 structurally, with no numeric publication success/failure.
    states.append(
        state_outcome(
            observed_state(received, "artifact_state"), {"correct"}, {"partial"}, sensitivity
        )
    )
    return conjunction(states)


def required_fact_ids(registry):
    return sorted(
        {
            m.fact_id
            for m in registry.memberships
            if m.required_within_path == "yes"
            and any(p.path_id == m.path_id and p.validity == "yes" for p in registry.paths)
        }
    )


def fact_any_route(data, arm, sensitivity=False):
    result = {}
    for fact in data.registry.facts:
        rows = [s for s in data.shared if s.fact_id == fact.fact_id]
        states = []
        for shared in rows:
            eligible = reference_eligibility(shared)
            received = arm.s4.get(f"{shared.fact_id}|{shared.worker_id}")
            states.append(
                eligible
                if eligible is not None
                else state_outcome(observed_state(received), {"correct"}, {"partial"}, sensitivity)
            )
        result[fact.fact_id] = disjunction(states)
    return result


def complete_received_paths(data, arm):
    if not data.registry.frozen_hash:
        return []
    states = path_outcomes(data.registry, fact_any_route(data, arm))
    return [p for p, state in states.items() if state == Outcome.SUCCESS]


def downstream_outcome(data, arm, sensitivity=False):
    paths = complete_received_paths(data, arm)
    if not paths:
        availability = question_path_outcome(data.registry, fact_any_route(data, arm))
        if not data.registry.frozen_hash:
            return Outcome.NON_IDENTIFIABLE
        return Outcome.INELIGIBLE if availability == Outcome.FAILURE else availability
    # Support must be judged for one of these RECEIVED paths, not an unreceived path.
    return disjunction(
        state_outcome(
            observed_state(arm.s5b.get(p)),
            {"fully_supported"},
            {"partially_supported"},
            sensitivity,
        )
        for p in paths
    )


def metric_units(data, sensitivity=False):
    """Shared upstream once; downstream dictionaries indexed by private arm ID."""
    from review_v3.schema import QuestionLabels

    data = QuestionLabels.model_validate(data.model_dump(mode="json"))
    qid = data.registry.question.question_id
    shared_names = ["access_coverage", "worker_public_expression_survival", "publication_survival"]
    output = {name: [] for name in shared_names}
    for shared in data.shared:
        key = f"{shared.fact_id}|{shared.worker_id}"
        ref = reference_eligibility(shared)
        access = (
            ref
            if ref is not None
            else state_outcome(observed_state(shared.s1), {"complete"}, {"partial"}, sensitivity)
        )
        expression_eligible = (
            ref if ref is not None else prerequisite(observed_state(shared.s1), {"complete"})
        )
        expression = (
            state_outcome(observed_state(shared.s2), {"correct"}, {"partial"}, sensitivity)
            if expression_eligible == Outcome.SUCCESS
            else expression_eligible
        )
        if shared.s3.publication_transition_type is None:
            publication = Outcome.MISSING
        elif shared.s3.publication_transition_type == "identity_alias":
            publication = Outcome.NA
        elif shared.s3.publication_transition_type == "unknown":
            before = prerequisite(observed_state(shared.s2), {"correct"})
            publication = Outcome.NON_IDENTIFIABLE if before == Outcome.SUCCESS else before
        else:
            before = prerequisite(observed_state(shared.s2), {"correct"})
            publication = (
                state_outcome(
                    observed_state(shared.s3), {"retained"}, {"partial_loss"}, sensitivity
                )
                if before == Outcome.SUCCESS
                else before
            )
        for name, state in zip(shared_names, (access, expression, publication), strict=True):
            output[name].append(Unit(qid, key, state))
    for arm_id, arm in data.arms.items():
        names = [
            "artifact_transmission_survival",
            "any_route_synthesizer_availability",
            "downstream_evidential_support",
            "fact_end_to_end_survival",
            "path_end_to_end_survival",
        ]
        for name in names:
            output[f"{name}:{arm_id}"] = []
        fact_chains = {}
        for shared in data.shared:
            key = f"{shared.fact_id}|{shared.worker_id}"
            received = arm.s4.get(key)
            before = prerequisite(shared.s3.artifact_fact_state, {"correct"})
            transmission = (
                state_outcome(
                    observed_state(received, "artifact_state"),
                    {"correct"},
                    {"partial"},
                    sensitivity,
                )
                if before == Outcome.SUCCESS
                else before
            )
            output[f"artifact_transmission_survival:{arm_id}"].append(Unit(qid, key, transmission))
            fact_chains.setdefault(shared.fact_id, []).append(
                fact_e2e(shared, received, sensitivity)
            )
        any_route = fact_any_route(data, arm, sensitivity)
        for fact, state in any_route.items():
            output[f"any_route_synthesizer_availability:{arm_id}"].append(Unit(qid, fact, state))
        fact_e2e_states = {fact: disjunction(states) for fact, states in fact_chains.items()}
        for fact in required_fact_ids(data.registry):
            output[f"fact_end_to_end_survival:{arm_id}"].append(
                Unit(qid, fact, fact_e2e_states.get(fact, Outcome.MISSING))
            )
        path_state = question_path_outcome(data.registry, fact_e2e_states)
        if not data.registry.frozen_hash:
            path_state = Outcome.NON_IDENTIFIABLE
        output[f"path_end_to_end_survival:{arm_id}"].append(Unit(qid, qid, path_state))
        output[f"downstream_evidential_support:{arm_id}"].append(
            Unit(qid, qid, downstream_outcome(data, arm, sensitivity))
        )
    return output


def summarize(units, structural_na_excluded=False):
    counts = Counter(u.outcome for u in units)
    evaluable = counts[Outcome.SUCCESS] + counts[Outcome.FAILURE]
    potential = len(units) - counts[Outcome.INELIGIBLE]
    if structural_na_excluded:
        potential -= counts[Outcome.NA]
    return {
        "potentially_eligible_n": potential,
        "evaluable_n": evaluable,
        "success_n": counts[Outcome.SUCCESS],
        "unclear_n": counts[Outcome.UNCLEAR],
        "missing_n": counts[Outcome.MISSING],
        "NA_n": counts[Outcome.NA],
        "non_identifiable_n": counts[Outcome.NON_IDENTIFIABLE],
        "ineligible_n": counts[Outcome.INELIGIBLE],
        "rate": counts[Outcome.SUCCESS] / evaluable if evaluable else None,
        "evaluability_coverage": evaluable / potential if potential else None,
    }


def aggregate(questions, sensitivity=False, scope=None):
    """Question macro primary; pooled micro secondary descriptive. No CI by default."""
    ids = [q.registry.question.question_id for q in questions]
    if any(q.label_origin not in ("synthetic", "adjudicated") for q in questions):
        raise ValueError("Lineage metrics require final adjudicated labels (or synthetic tests)")
    if any(q.label_origin == "adjudicated" for q in questions) and scope is None:
        raise ValueError("Human-decided case inclusion manifest required for real metrics")
    if len(ids) != len(set(ids)):
        raise ValueError("Question cannot be duplicated/Study 1 and 2 pooled as independent")
    if scope is not None:
        required = set(scope.included_case_ids) - set(scope.descriptive_only_case_ids)
        if not required <= set(ids):
            raise ValueError("Human primary scope incomplete")
        questions = [q for q in questions if q.registry.question.question_id in required]
    grouped = {}
    for question in questions:
        for name, units in metric_units(question, sensitivity).items():
            grouped.setdefault(name, {})[question.registry.question.question_id] = units
    results = {}
    for name, by_question in grouped.items():
        structural_na = name == "publication_survival"
        summaries = {qid: summarize(units, structural_na) for qid, units in by_question.items()}
        rates = [s["rate"] for s in summaries.values() if s["rate"] is not None]
        results[name] = {
            "question_macro_primary": mean(rates) if rates else None,
            "evaluable_question_n": len(rates),
            "excluded_question_n": len(summaries) - len(rates),
            "question_summaries": summaries,
            "micro_secondary_descriptive": summarize(
                [u for units in by_question.values() for u in units], structural_na
            ),
        }
    return results
