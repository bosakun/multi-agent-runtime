"""Mechanical pilot preparation tests; fixtures are invented, not human labels."""

import hashlib
import json

import pytest
from review_v3.pilot_materials_v1.prepare import (
    MARKER,
    SALT,
    pilot_b_projection,
    raw_material,
    select_ids,
    templates,
    worklist,
)
from review_v3.pilot_materials_v1.verify import REQUIRED_COVERAGE, validate_b_sources
from review_v3.storage import digest, exclusive


def row():
    return {
        "_id": "invented-id",
        "question": "Which year?",
        "context": [["Invented", ["Opened in 2012.", "Closed in 2014."]]],
        "answer": "2012",
        "supporting_facts": [["Invented", 0]],
        "worker_output": "must not copy",
        "score": 1,
    }


def test_selection_only_ids_and_deterministic():
    ids = [f"qa-{i}" for i in range(40)]
    excluded = ids[:10]
    a, eligible = select_ids(ids, excluded)
    b, _ = select_ids(list(reversed(ids)), list(reversed(excluded)))
    assert a == b
    assert len(a) == 6 and not set(a) & set(excluded)
    assert a == sorted(eligible, key=lambda q: hashlib.sha256((SALT + q).encode()).hexdigest())[:6]
    assert digest(eligible) == digest(sorted(set(ids) - set(excluded)))


def test_duplicate_ids_rejected():
    with pytest.raises(ValueError):
        select_ids(["a", "a"], [])


def test_all_exclusion_categories_are_removed_without_content():
    groups = {
        "main30": ["main-1", "main-2"],
        "study2_main": ["main-1"],
        "study2_smoke": ["smoke"],
        "historical_calibration": ["calibration"],
        "old_review_calibration": ["old-calibration"],
        "other_guideline": ["guideline"],
    }
    excluded = {q for values in groups.values() for q in values}
    selected, eligible = select_ids(sorted(excluded) + [f"new-{i}" for i in range(12)], excluded)
    for values in groups.values():
        assert not set(selected) & set(values)
    assert len(eligible) == 12


def test_unknown_stage_or_non_synthetic_input_rejected():
    with pytest.raises(ValueError):
        pilot_b_projection({"marker": MARKER}, "S6")
    with pytest.raises(ValueError):
        pilot_b_projection({"marker": "real study data"}, "S1")


def test_b_coverage_and_answer_key_separation_validation():
    # Artificial structure fixture, not supplied teaching labels or real packets.
    keys = [{"vignette_id": "synthetic", "coverage": sorted(REQUIRED_COVERAGE)}]
    sources = {
        phase: [
            {
                "vignette_id": "synthetic",
                "marker": MARKER,
                "question": {"en": "Invented question", "ja": "人工の質問"},
                **({"final_output": {}} if phase == "S5" else {}),
                **({"actual_synthesizer_input": {}} if phase in {"S4", "S5"} else {}),
            }
        ]
        for phase in ["S1", "S2", "S3", "S4", "S5"]
    }
    assert validate_b_sources(sources, keys) == 1
    sources["S1"][0]["author_key"] = {"intended_label": "correct"}
    with pytest.raises(AssertionError):
        validate_b_sources(sources, keys)


def test_raw_projection_no_gold_outputs_or_registry():
    r1 = raw_material(row(), "PA-01")
    assert set(r1) == {"case_alias", "question", "reference_sentences"}
    assert len(r1["reference_sentences"]) == 2
    assert set(r1["reference_sentences"][0]) == {
        "sentence_id",
        "title",
        "sentence_index",
        "sentence_text",
    }
    assert "answer" not in json.dumps(r1) and "must not copy" not in json.dumps(r1)


def test_r1_worklist_stage_limited():
    r1 = raw_material(row(), "PA-01")
    for entry in worklist(r1, "R1"):
        assert set(entry) == {
            "case_alias",
            "material_pointer",
            "english_original",
            "english_hash",
            "allowed_translation_context",
        }
        assert (
            entry["english_hash"] == hashlib.sha256(entry["english_original"].encode()).hexdigest()
        )
        assert not entry["material_pointer"].startswith("/benchmark_alignment")


def test_r2_gold_only_added():
    r2 = {
        **raw_material(row(), "PA-01"),
        "benchmark_alignment": {
            "gold_answer": row()["answer"],
            "gold_supporting_facts": row()["supporting_facts"],
        },
    }
    assert set(r2) == {"case_alias", "question", "reference_sentences", "benchmark_alignment"}
    assert any(x["material_pointer"].endswith("gold_answer") for x in worklist(r2, "R2"))
    assert "must not copy" not in json.dumps(r2)


@pytest.mark.parametrize("phase", ["S1", "S2", "S3", "S4", "S5"])
def test_synthetic_progressive_sources_no_key(phase):
    case = {
        "vignette_id": "synthetic",
        "marker": MARKER,
        "question": {"en": "Q", "ja": "問い"},
        "reference": [],
        "teaching_reference": {},
        "actual_worker_input_sentence_ids": {},
        "worker_public_expression": {},
        "publication_transition_type": "identity_alias",
        "published_artifact": {},
        "actual_synthesizer_input": {},
        "final_output": {"en": "secret"},
        "author_key": {"intended_label": "correct", "explanation": "author only"},
    }
    value = pilot_b_projection(case, phase)
    assert value["marker"] == MARKER
    assert "author_key" not in value and "intended_label" not in json.dumps(value)
    assert ("final_output" in value) == (phase == "S5")
    assert ("worker_public_expression" in value) == (phase != "S1")
    assert ("actual_synthesizer_input" in value) == (phase in ("S4", "S5"))


def test_templates_no_people_or_human_labels():
    value = templates()
    assert len(value) == 6
    assert value["reviewer-profile"]["reviewer_id"] is None
    assert value["pilot-human-authorization"]["signed_by"] is None
    assert value["pilot-ambiguity-log"]["entries"] == []


def test_exclusive_preserves_old_assets(tmp_path):
    path = tmp_path / "synthetic.json"
    exclusive(path, {"invented": True})
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        exclusive(path, {"invented": False})
    assert path.read_bytes() == before
