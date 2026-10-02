"""Invented labels for mechanical tests only; not Human Review/HotpotQA results."""

from datetime import UTC, datetime

from review_v3.provenance import text_hash
from review_v3.schema import (
    S0,
    S1,
    S2,
    S3,
    S4,
    ArmLabels,
    Fact,
    Membership,
    Question,
    QuestionLabels,
    ReasoningPath,
    Registry,
    RegistryJudgment,
    S5a,
    S5b,
    Sentence,
    SharedLineage,
    SupportSet,
)
from review_v3.workflow import Workflow, frozen_registry


def registry(qid="synthetic-q", n=2):
    question = Question(
        question_id=qid,
        question_text="Synthetic question; not a real QA item",
        source_hash="synthetic-source",
        registry_version="synthetic-v1",
    )
    sentences = [
        Sentence(
            sentence_id=f"s{i}",
            title="Invented",
            sentence_index=i,
            text=f"Invented fact {i}",
            text_hash=text_hash(f"Invented fact {i}"),
        )
        for i in range(n)
    ]
    facts = [
        Fact(
            fact_id=f"f{i}",
            fact_text=f"Invented fact {i}",
            fact_type="atomic_fact",
            reference_basis="raw_discovery",
        )
        for i in range(n)
    ]
    sets = [
        SupportSet(
            support_set_id=f"set{i}",
            fact_id=f"f{i}",
            evidence_sentence_ids=[f"s{i}"],
            support_set_sufficient="yes",
        )
        for i in range(n)
    ]
    paths = [
        ReasoningPath(
            path_id="p1",
            path_basis="raw_discovered_alternative",
            target_answer="Invented",
            validity="yes",
        )
    ]
    members = [
        Membership(
            question_id=qid,
            path_id="p1",
            fact_id=f"f{i}",
            required_within_path="yes",
            support_set_ids=[f"set{i}"],
        )
        for i in range(n)
    ]
    judgment = RegistryJudgment(
        reviewer_id="synthetic-person",
        registry_phase="FINAL",
        registry_version="synthetic-v1",
        judgment_status="adjudicated",
        rationale="Invented fixture",
        timestamp=datetime(2020, 1, 1, tzinfo=UTC),
        source_hashes={"synthetic": "fixture"},
    )
    return Registry(
        question=question,
        sentences=sentences,
        facts=facts,
        support_sets=sets,
        paths=paths,
        memberships=members,
        judgments=[judgment],
    )


def workflow(reg=None):
    flow = Workflow(reviewer_ids=("synthetic-r1", "synthetic-r2"), synthetic=True)
    for phase in ("R1", "R2"):
        for reviewer in flow.reviewer_ids:
            flow = flow.lock(reviewer, phase, {"fixture": phase}, "synthetic-v1")
        flow = flow.advance(phase + "_LOCKED")
        flow = flow.advance("R2_OPEN" if phase == "R1" else "ADJUDICATION")
    flow = flow.advance("REGISTRY_FROZEN", reg or registry(), "synthetic sign-off ONLY")
    return flow.freeze_codebook("synthetic-v1", {"synthetic": True}, True, "synthetic ONLY")


def labels(qid="synthetic-q", n=2, transition="identity_alias", arms=("arm-x", "arm-y", "arm-z")):
    reg = registry(qid, n)
    reg = frozen_registry(reg, workflow(reg))
    shared, arm_models = [], {}
    for fact in reg.facts:
        common = dict(
            question_id=qid,
            fact_id=fact.fact_id,
            worker_id="worker-x",
            applicability="applicable",
            reviewer_id="synthetic-r1",
            codebook_version="synthetic-v1",
        )
        s3 = (
            S3(
                **{
                    **common,
                    "applicability": "not_applicable",
                    "applicability_reason": "no_separate_transition",
                },
                state="NA",
                publication_transition_type=transition,
                artifact_fact_state="correct",
            )
            if transition == "identity_alias"
            else S3(
                **common,
                state="retained" if transition == "separate_records" else "unclear",
                publication_transition_type=transition,
                artifact_fact_state="correct",
            )
        )
        shared.append(
            SharedLineage(
                fact_id=fact.fact_id,
                worker_id="worker-x",
                s0=S0(**common, state="complete"),
                s1=S1(**common, state="complete"),
                s2=S2(**common, state="correct"),
                s3=s3,
            )
        )
    for arm_id in arms:
        s4, s5a = {}, {}
        for row in shared:
            common = dict(
                question_id=qid,
                fact_id=row.fact_id,
                arm=arm_id,
                applicability="applicable",
                reviewer_id="synthetic-r1",
                codebook_version="synthetic-v1",
            )
            s4[f"{row.fact_id}|worker-x"] = S4(
                **common,
                worker_id="worker-x",
                state="correct",
                artifact_state="correct",
                supplementary_state="absent",
                machine_payload_match="match",
                received_via="artifact",
            )
            s5a[row.fact_id] = S5a(**common, state="not_asserted")
        s5b = {
            "p1": S5b(
                question_id=qid,
                arm=arm_id,
                path_id="p1",
                state="fully_supported",
                applicability="applicable",
                reviewer_id="synthetic-r1",
                codebook_version="synthetic-v1",
            )
        }
        arm_models[arm_id] = ArmLabels(s4=s4, s5a=s5a, s5b=s5b)
    return QuestionLabels(registry=reg, shared=shared, arms=arm_models, label_origin="synthetic")


def changed(data, stage, state, fact="f0", arm="arm-x", **extras):
    value = data.model_dump(mode="json")
    if stage in ("s0", "s1", "s2", "s3"):
        target = next(row for row in value["shared"] if row["fact_id"] == fact)[stage]
    elif stage == "s4":
        target = value["arms"][arm][stage][fact + "|worker-x"]
    elif stage == "s5a":
        target = value["arms"][arm][stage][fact]
    else:
        target = value["arms"][arm][stage]["p1"]
    target.update(state=state, **extras)
    return QuestionLabels.model_validate(value)
