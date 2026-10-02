"""Explicit OR/AND with missing/non-identifiable distinct from failure."""

from enum import StrEnum

from review_v3.schema import Registry


class Outcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    UNCLEAR = "unclear"
    MISSING = "missing"
    NA = "NA"
    NON_IDENTIFIABLE = "non_identifiable"
    INELIGIBLE = "ineligible"


UNCERTAINTY = (Outcome.MISSING, Outcome.UNCLEAR, Outcome.NON_IDENTIFIABLE, Outcome.NA)


def disjunction(values):
    values = list(values)
    if Outcome.SUCCESS in values:
        return Outcome.SUCCESS
    for unknown in UNCERTAINTY:
        if unknown in values:
            return unknown
    if values and all(v == Outcome.INELIGIBLE for v in values):
        return Outcome.INELIGIBLE
    return Outcome.FAILURE if values else Outcome.MISSING


def conjunction(values):
    values = list(values)
    # For lineage coverage all applicable stages must be observable, even if one failed.
    for unknown in UNCERTAINTY:
        if unknown in values:
            return unknown
    if not values:
        return Outcome.MISSING  # No vacuous valid path.
    if Outcome.INELIGIBLE in values:
        return Outcome.INELIGIBLE
    return Outcome.SUCCESS if all(v == Outcome.SUCCESS for v in values) else Outcome.FAILURE


def state_outcome(state, success, partial=(), sensitivity=False):
    if state is None:
        return Outcome.MISSING
    if state == "unclear":
        return Outcome.UNCLEAR
    if state == "NA":
        return Outcome.NA
    return (
        Outcome.SUCCESS if state in success or sensitivity and state in partial else Outcome.FAILURE
    )


def support_access(registry: Registry, fact_id, actual_ids, support_set_ids=None):
    if actual_ids is None:
        return "unclear"  # Missing input never means documented none.
    sets = [
        s
        for s in registry.support_sets
        if s.fact_id == fact_id and (support_set_ids is None or s.support_set_id in support_set_ids)
    ]
    known = [s for s in sets if s.support_set_sufficient == "yes"]
    if any(set(s.evidence_sentence_ids) <= set(actual_ids) for s in known):
        return "complete"
    if any(s.support_set_sufficient in (None, "unclear") for s in sets) or not known:
        return "unclear"
    if any(set(s.evidence_sentence_ids) & set(actual_ids) for s in known):
        return "partial"
    return "none"


def path_outcomes(registry, fact_outcomes):
    result = {}
    for path in registry.paths:
        if path.validity == "no":
            continue
        if path.validity != "yes":
            result[path.path_id] = Outcome.MISSING if path.validity is None else Outcome.UNCLEAR
            continue
        members = [m for m in registry.memberships if m.path_id == path.path_id]
        required = [m for m in members if m.required_within_path == "yes"]
        support_sets = {s.support_set_id: s for s in registry.support_sets}
        states = []
        for member in required:
            candidates = [
                support_sets[sid].support_set_sufficient for sid in member.support_set_ids
            ]
            if "yes" in candidates:
                states.append(fact_outcomes.get(member.fact_id, Outcome.MISSING))
            else:
                states.append(Outcome.MISSING if None in candidates else Outcome.UNCLEAR)
        states += [
            Outcome.MISSING if m.required_within_path is None else Outcome.UNCLEAR
            for m in members
            if m.required_within_path in (None, "unclear")
        ]
        result[path.path_id] = conjunction(states)
    return result


def question_path_outcome(registry, fact_outcomes):
    if registry.paths and all(p.validity == "no" for p in registry.paths):
        return Outcome.INELIGIBLE
    return disjunction(path_outcomes(registry, fact_outcomes).values())
