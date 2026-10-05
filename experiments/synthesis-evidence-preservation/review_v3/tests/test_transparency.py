"""Invented declarations only. No real people, scope decisions, translations or labels."""

import pytest
from pydantic import ValidationError
from review_v3.bilingual import TranslationAsset
from review_v3.codebook import CodebookRevision
from review_v3.storage import ReviewStore, digest, file_hash
from review_v3.transparency import MainReviewSignoff, ReviewerProfile
from synthetic import registry
from test_bilingual import artificial_asset
from test_codebook_pilot import TIME, clearance, definition_v1, main_signoff, unfrozen_main


@pytest.mark.parametrize("relationship", [
    "none", "family", "academic_advisor", "friend_or_peer", "collaborator", "other",
])
def test_relationship_is_not_annotation_independence(relationship):
    value = main_signoff().reviewers[0].model_dump()
    value["relationship_to_author"] = [relationship]
    assert ReviewerProfile(**value).relationship_to_author == [relationship]
    value["relationship_to_author"] = ["none", "family"]
    with pytest.raises(ValidationError):
        ReviewerProfile(**value)


@pytest.mark.parametrize("method", [
    "human_manual", "machine_translation", "llm_assisted_translation", "other",
])
def test_translation_provenance_and_hash_are_preserved(method):
    value = artificial_asset(registry()).model_dump(mode="json", exclude={"frozen_hash"})
    value["translation_method"] = method
    value["translation_system_metadata"] = {"system": "invented", "version": "test-only"}
    asset = TranslationAsset(**value, frozen_hash=digest(value))
    assert asset.translation_method == method
    # No rule demands that the preparer and reviewer be different people.
    assert asset.translation_prepared_by_or_system == asset.translation_verified_by
    value["verification_method"] = "Changed provenance without re-freezing"
    with pytest.raises(ValidationError):
        TranslationAsset(**value, frozen_hash=asset.frozen_hash)


def revision(**updates):
    return CodebookRevision(**dict(
        change_id="invented-revision", old_definition_hash="old", new_definition_hash="new",
        old_version="0.2.0", new_version="0.3.0", reason="Invented ambiguity",
        affected_fields=["S2"], affected_rule_ids=["GEN-PART-001"],
        affected_pilot_units=["invented-1", "invented-2"],
        impact_and_reannotation="All affected units under one new version",
        semantic_rules_changed=True, old_annotation_hashes={"old-ballot": "hash"},
        reannotation_strategy="all_affected_units",
        reannotated_pilot_units=["invented-1", "invented-2"], timestamp=TIME,
    ) | updates)


def test_semantic_revision_rejects_selective_cases_and_requires_old_ballots():
    assert revision().semantic_rules_changed
    for updates in (
        {"old_annotation_hashes": {}}, {"reannotated_pilot_units": ["invented-1"]},
        {"reannotation_strategy": None},
    ):
        with pytest.raises(ValidationError):
            revision(**updates)
    assert revision(
        reannotation_strategy="new_independent_batch", reannotated_pilot_units=[],
        new_independent_batch_id="new-invented-batch",
    ).new_independent_batch_id


def test_main_requires_all_human_confirmations_and_hash_matches():
    value = main_signoff().model_dump()
    with pytest.raises(ValidationError):
        MainReviewSignoff(**(value | {"confirmed_items": value["confirmed_items"][:-1]}))
    with pytest.raises(ValueError, match="HUMAN preflight"):
        unfrozen_main().freeze_codebook(
            "1.0.0", definition_v1().model_dump(), True, "SYNTHETIC ONLY", clearance()
        )
    invalid = main_signoff().model_copy(update={"translation_policy_hash": "b" * 64})
    with pytest.raises(ValueError):
        unfrozen_main().freeze_codebook(
            "1.0.0", definition_v1().model_dump(), True, "SYNTHETIC ONLY",
            clearance(main_signoff=invalid),
        )


@pytest.mark.parametrize("n", [28, 30])
def test_scope_is_explicit_human_input_not_a_default(n):
    value = main_signoff().model_dump()
    value["study1_main_n"] = n
    value["study1_scope"]["included_case_ids"] = [f"invented-{i}" for i in range(n)]
    value["study1_scope"]["iaa_eligible_case_ids"] = [f"invented-{i}" for i in range(n)]
    signoff = MainReviewSignoff(**value)
    assert signoff.study1_main_n == n
    del value["study1_main_n"]
    with pytest.raises(ValidationError):
        MainReviewSignoff(**value)


def test_known_results_are_disclosed_not_claimed_fully_blind():
    context = main_signoff().adjudicator_contexts[0]
    assert context.prior_result_exposure and context.allocation_blinded_where_feasible
    assert context.disclosure_notes


@pytest.mark.parametrize("use_third", [False, True])
def test_optional_third_adjudicator_supports_main_signoff(use_third):
    value = main_signoff().model_dump()
    value["third_adjudicator_used"] = use_third
    if not use_third:
        value["adjudicator_contexts"] = []
    signoff = MainReviewSignoff(**value)
    assert bool(signoff.adjudicator_contexts) == use_third
    sealed = unfrozen_main().freeze_codebook(
        "1.0.0", definition_v1().model_dump(), True, "SYNTHETIC ONLY",
        clearance(main_signoff=signoff),
    )
    assert sealed.main_signoff_hash == signoff.content_hash


@pytest.mark.parametrize("policy", ["missing", "true_without_context", "false_with_context"])
def test_third_adjudicator_policy_must_be_explicit_and_consistent(policy):
    value = main_signoff().model_dump()
    if policy == "missing":
        del value["third_adjudicator_used"]
    elif policy == "true_without_context":
        value["adjudicator_contexts"] = []
    else:
        value["third_adjudicator_used"] = False
    with pytest.raises(ValidationError):
        MainReviewSignoff(**value)


def test_signoffs_and_profiles_are_append_only_author_records(tmp_path):
    store = ReviewStore(tmp_path)
    record = main_signoff()
    store.append("main_review_signoffs", "invented", "v1", record.model_dump(mode="json"))
    old_hash = file_hash(tmp_path / "main_review_signoffs/invented/v1.json")
    with pytest.raises(FileExistsError):
        store.append("main_review_signoffs", "invented", "v1", {})
    assert file_hash(tmp_path / "main_review_signoffs/invented/v1.json") == old_hash
