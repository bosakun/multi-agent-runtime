"""Observed states are immutable inputs; these events are mechanically derived."""

from dataclasses import asdict, dataclass

from review_v3 import RULE_VERSION
from review_v3.logic import Outcome
from review_v3.metrics import complete_received_paths, downstream_outcome, observed_state
from review_v3.storage import digest


@dataclass(frozen=True)
class Event:
    event_id: str
    stage: str
    labels: tuple[str, ...]
    scope: dict
    prerequisite_references: tuple[str, ...]
    supporting_record_locations: tuple[str, ...]
    rule_version: str = RULE_VERSION


def derive(data, arm_id):
    from review_v3.schema import QuestionLabels

    data = QuestionLabels.model_validate(data.model_dump(mode="json"))
    arm = data.arms[arm_id]
    qid = data.registry.question.question_id
    events, unknown_stages = [], []

    def add(stage, labels, scope, pointers=(), prereqs=()):
        if not labels:
            return
        # Labels on a single transition share event_id, hence mismatch+distortion count once.
        identity = {"stage": stage, "scope": scope, "rule_version": RULE_VERSION}
        events.append(
            Event(
                digest(identity),
                stage,
                tuple(sorted(set(labels))),
                scope,
                tuple(prereqs),
                tuple(pointers),
            )
        )

    def unknown(stage, state, structural=False):
        if not structural and state in (None, "unclear", "NA"):
            unknown_stages.append(stage)

    for shared in data.shared:
        key = f"{shared.fact_id}|{shared.worker_id}"
        received = arm.s4.get(key)
        scope = {
            "question_id": qid,
            "fact_id": shared.fact_id,
            "worker_id": shared.worker_id,
            "arm": None,
            "route": None,
        }
        s0, s1, s2, s3 = shared.s0, shared.s1, shared.s2, shared.s3
        # Blank/inapplicable metadata never becomes an observed semantic assertion.
        observed = {
            stage: observed_state(record)
            for stage, record in (("S0", s0), ("S1", s1), ("S2", s2), ("S3", s3))
        }
        for stage in ("S0", "S1", "S2"):
            unknown(
                stage,
                observed[stage],
                {"S0": s0, "S1": s1, "S2": s2}[stage].applicability == "not_applicable",
            )
        if observed["S0"] == "absent":
            add(
                "S0",
                ["reference_evidence_absent"],
                {"question_id": qid, "fact_id": shared.fact_id},
                s0.evidence_pointer,
            )
        if observed["S0"] == "complete":
            access = {"partial": "access_partial", "none": "access_absent"}.get(observed["S1"])
            add("S1", [access] if access else [], scope, s1.evidence_pointer, ("S0=complete",))
        if observed["S0"] == "complete" and observed["S1"] == "complete":
            label = {
                "absent": "expression_absent_after_complete_access",
                "distorted": "expression_distorted_after_complete_access",
            }.get(observed["S2"])
            add("S2", [label] if label else [], scope, s2.evidence_pointer, ("S0/S1=complete",))
        if s3.publication_transition_type in (None, "unknown"):
            unknown_stages.append("S3")
        else:
            unknown("S3", observed["S3"], s3.publication_transition_type == "identity_alias")
        if s3.publication_transition_type == "separate_records" and observed["S2"] == "correct":
            label = {
                "partial_loss": "publication_partial_loss",
                "lost": "publication_loss",
                "distorted": "publication_distortion",
            }.get(observed["S3"])
            add(
                "S3",
                [label] if label else [],
                scope,
                s3.evidence_pointer,
                ("separate_records", "S2=correct"),
            )
        s4_scope = {**scope, "arm": arm_id, "route": "artifact"}
        unknown(
            "S4",
            observed_state(received),
            received is not None and received.applicability == "not_applicable",
        )
        unknown("S4", s3.artifact_fact_state)
        if (
            received
            and received.applicability == "applicable"
            and s3.artifact_fact_state == "correct"
        ):
            labels = []
            if (
                received.machine_payload_match == "mismatch"
                and received.mismatch_fact_related is True
            ):
                labels.append("transmission_record_mismatch")
            label = {
                "partial": "transmission_partial_loss",
                "distorted": "transmission_distortion",
            }.get(observed_state(received, "artifact_state"))
            if label:
                labels.append(label)
            add("S4", labels, s4_scope, received.evidence_pointer, ("artifact_fact_state=correct",))
        final = arm.s5a.get(shared.fact_id)
        if final:
            unknown("S5", observed_state(final), final.applicability == "not_applicable")
            if observed_state(received) == "correct" and observed_state(final) == "contradicted":
                add(
                    "S5",
                    ["final_output_contradicts_received_fact"],
                    {"question_id": qid, "fact_id": shared.fact_id, "arm": arm_id},
                    final.evidence_pointer,
                    ("S4=correct",),
                )
        else:
            unknown_stages.append("S5")
    received_paths = complete_received_paths(data, arm)
    unsupported_paths = []
    support_pointers = []
    for path in received_paths:
        support = arm.s5b.get(path)
        unknown(
            "S5",
            observed_state(support),
            support is not None and support.applicability == "not_applicable",
        )
        if observed_state(support) == "unsupported":
            unsupported_paths.append(path)
            support_pointers.extend(support.evidence_pointer)
    if (
        received_paths
        and unsupported_paths == received_paths
        and downstream_outcome(data, arm) == Outcome.FAILURE
    ):
        add(
            "S5",
            ["answer_unsupported_despite_complete_received_path"],
            {"question_id": qid, "path_ids": received_paths, "arm": arm_id},
            support_pointers,
            ("complete valid frozen received path", "all received paths unsupported"),
        )
    # Duplicate facts may support multiple paths; event identity uses actual transition scope.
    unique = {event.event_id: event for event in events}
    events = sorted(unique.values(), key=lambda e: (e.stage, e.event_id))
    if events:
        earliest = events[0].stage
        first = "undetermined" if any(stage < earliest for stage in unknown_stages) else earliest
    else:
        first = "undetermined" if unknown_stages else "no_failure_observed"
    return {
        "events": [asdict(event) for event in events],
        "first_observable_failure_stage": first,
        "failure_count": len(events),
        "has_multiple_distinct_observable_failures": len(events) > 1,
        "undetermined_stages": sorted(set(unknown_stages)),
        "rule_version": RULE_VERSION,
        "interpretation": "observable events, not internal reasoning or causal attribution",
    }


def derive_question(data):
    """Shared event IDs are counted ONCE across all arms; arm diagnostics remain separate."""
    results = {arm: derive(data, arm) for arm in data.arms}
    distinct = {
        event["event_id"]: event for result in results.values() for event in result["events"]
    }
    return {
        "by_arm": results,
        "distinct_question_events": list(distinct.values()),
        "failure_count": len(distinct),
        "has_multiple_distinct_observable_failures": len(distinct) > 1,
    }
