import pytest
from pydantic import ValidationError
from review_v3.logic import Outcome, path_outcomes, question_path_outcome, support_access
from review_v3.schema import S2, S3, Registry, Scope
from review_v3.storage import ReviewStore, digest
from review_v3.workflow import Workflow, frozen_registry
from synthetic import registry, workflow


def test_schema_separate_objects_and_references():
    reg = registry()
    assert reg.facts[0].fact_id != reg.sentences[0].sentence_id
    assert Registry.model_validate_json(reg.model_dump_json()) == reg
    value = reg.model_dump()
    value["support_sets"][0]["evidence_sentence_ids"] = ["unknown"]
    with pytest.raises(ValidationError):
        Registry.model_validate(value)


def test_support_set_or():
    reg = registry()
    value = reg.model_dump()
    value["support_sets"].append(
        {
            "support_set_id": "alternative",
            "fact_id": "f0",
            "evidence_sentence_ids": ["s1"],
            "support_set_sufficient": "yes",
        }
    )
    reg = Registry.model_validate(value)
    assert support_access(reg, "f0", ["s1"]) == "complete"
    assert support_access(reg, "f0", []) == "none"
    assert support_access(reg, "f0", None) == "unclear"


def test_support_set_sentences_and():
    value = registry().model_dump()
    value["support_sets"][0]["evidence_sentence_ids"] = ["s0", "s1"]
    reg = Registry.model_validate(value)
    assert support_access(reg, "f0", ["s0"]) == "partial"
    assert support_access(reg, "f0", ["s0", "s1"]) == "complete"


def test_path_facts_and_and_alternative_paths_or():
    reg = registry()
    states = {"f0": Outcome.SUCCESS, "f1": Outcome.FAILURE}
    assert question_path_outcome(reg, states) == Outcome.FAILURE
    value = reg.model_dump()
    value["paths"].append(
        {
            "path_id": "p2",
            "path_basis": "raw_discovered_alternative",
            "target_answer": "Invented",
            "validity": "yes",
        }
    )
    member = dict(value["memberships"][0], path_id="p2")
    value["memberships"].append(member)
    reg = Registry.model_validate(value)
    assert path_outcomes(reg, states)["p1"] == Outcome.FAILURE
    assert question_path_outcome(reg, states) == Outcome.SUCCESS


def test_missing_unclear_not_identical():
    blank = S2(question_id="q")
    unclear = S2(question_id="q", state="unclear")
    assert blank.state is None and unclear.state == "unclear"
    with pytest.raises(ValidationError):
        S2(question_id="q", state="correct", first_failure="S2")


def test_identity_alias_rules():
    with pytest.raises(ValidationError):
        S3(question_id="q", publication_transition_type="identity_alias", state="retained")
    valid = S3(
        question_id="q",
        publication_transition_type="identity_alias",
        state="NA",
        applicability="not_applicable",
        applicability_reason="no_separate_transition",
    )
    assert valid.state == "NA"


def test_registry_order_and_gold_gates():
    flow = Workflow(reviewer_ids=("r1", "r2"))
    with pytest.raises(ValueError):
        flow.authorize("R2", "r1")
    with pytest.raises(ValueError):
        flow.advance("REGISTRY_FROZEN", registry(), "human")
    flow = flow.lock("r1", "R1", {"candidate": []}, "v1")
    with pytest.raises(ValueError):
        flow.advance("R1_LOCKED")
    flow = flow.lock("r2", "R1", {"candidate": []}, "v1").advance("R1_LOCKED").advance("R2_OPEN")
    flow.authorize("R2", "r1")
    with pytest.raises(ValueError):
        flow.authorize("S1", "r1")


def test_progressive_own_locks_and_immutable():
    flow = workflow()
    flow.authorize("S1", "synthetic-r1")
    with pytest.raises(ValueError):
        flow.authorize("S2", "synthetic-r1")
    flow = flow.lock("synthetic-r1", "S1", {"invented": "complete"}, "v1")
    assert flow.locks[-1].content_hash == digest({"invented": "complete"})
    assert flow.locks[-1].timestamp
    flow.authorize("S2", "synthetic-r1")
    with pytest.raises(ValueError):
        flow.authorize("S2", "synthetic-r2")
    with pytest.raises(ValueError):
        flow.lock("synthetic-r1", "S1", {}, "v2")


def test_frozen_registry_mutation_rejected():
    reg = registry()
    flow = workflow(reg)
    sealed = frozen_registry(reg, flow)
    value = sealed.model_dump()
    value["facts"][0]["fact_text"] = "Silent mutation"
    with pytest.raises(ValidationError):
        Registry.model_validate(value)
    altered = reg.model_copy(update={"facts": []})
    with pytest.raises(ValueError):
        flow.verify_registry(altered)


def test_codebook_and_calibration_gate():
    flow = workflow().model_copy(update={"codebook_hash": None})
    with pytest.raises(ValueError):
        flow.authorize("S1", "synthetic-r1")
    with pytest.raises(ValueError):
        workflow().freeze_codebook("v2", {}, True, "human")


def test_scope_external_explicit_and_prior_exposure():
    scope = Scope(
        included_case_ids=["q1", "q2"],
        iaa_eligible_case_ids=["q1"],
        descriptive_only_case_ids=["q2"],
        decision_reason="Synthetic example",
    )
    assert len(scope.included_case_ids) == 2  # Tool does not select 30/28.
    with pytest.raises(ValidationError):
        Scope(**{**scope.model_dump(), "prior_exposure_by_reviewer": {"r1": ["q1"]}})


def test_independent_store_adjudication_never_overwrites(tmp_path):
    store = ReviewStore(tmp_path)
    store.append("stage_labels_reviewer1", "q", "v1", {"synthetic": "partial"})
    store.append("final_adjudicated_labels", "q", "v1", {"synthetic": "correct"})
    assert store.load("stage_labels_reviewer1", "q", "v1")["synthetic"] == "partial"
    with pytest.raises(FileExistsError):
        store.append("stage_labels_reviewer1", "q", "v1", {})
    with pytest.raises(ValueError):
        store.append("adjudication_log", "../../other", "v1", {})
