"""Artificial display/hash fixtures only. No real translation or human labels."""

import json

import pytest
from pydantic import ValidationError
from review_v3.bilingual import TranslationAsset, display_texts, text_hash
from review_v3.packets import build_packet, project
from review_v3.schema import S2
from review_v3.storage import digest, read
from review_v3.workflow import Workflow, frozen_registry
from synthetic import registry, workflow
from test_packets_preservation import scope, source


def artificial_asset(reg):
    aliases = {"question": "anonymous", "arm": "anonymous-arm", "worker_0": "worker-1"}
    texts = {}
    for phase in ("R1", "R2", "S1", "S2", "S3", "S4", "S5"):
        materials = project(source(reg), reg, phase, "B", aliases)
        texts.update({(p, text_hash(t)): t for p, t in display_texts(materials)})
    pairs = [
        {
            "english_original": original,
            "japanese_translation": f"人工表示-{i}",
            "english_sha256": hashed,
            "japanese_sha256": text_hash(f"人工表示-{i}"),
            "source_pointers": [f"AUTHOR-ONLY/{i}"],
            "display_pointers": [pointer],
        }
        for i, ((pointer, hashed), original) in enumerate(texts.items())
    ]
    value = dict(
        version="synthetic-ja-v1",
        review_mode="main",
        question_id=reg.question.question_id,
        pairs=pairs,
        preparation_method="Artificial non-semantic test values only",
        translation_method="other",
        translation_prepared_by_or_system="SYNTHETIC ONLY",
        translation_verified_by="SYNTHETIC ONLY",
        verification_method="Invented metadata; no semantic verification",
        translation_system_metadata={},
        human_approved_by="SYNTHETIC ONLY",
        frozen_at="2020-01-01T00:00:00Z",
    )
    value["frozen_hash"] = digest(value)
    return TranslationAsset.model_validate(value)


def test_real_packet_requires_translations_before_creating_output(tmp_path):
    reg = registry()
    with pytest.raises(ValueError, match="pre-frozen bilingual"):
        build_packet(
            source(reg),
            Workflow(reviewer_ids=("r1", "r2")),
            reg,
            "R1",
            "r1",
            tmp_path / "missing",
            scope=scope(reg),
        )
    assert not (tmp_path / "missing").exists()


def test_both_reviewers_receive_same_fixed_pairs_raw_unchanged(tmp_path):
    reg = registry()
    asset = artificial_asset(reg)
    flow = Workflow(reviewer_ids=("r1", "r2")).bind_translations(asset)
    packets = [
        build_packet(
            source(reg),
            flow,
            reg,
            "R1",
            r,
            tmp_path / r,
            case_alias="same-case",
            scope=scope(reg),
            translations=asset,
        )
        for r in flow.reviewer_ids
    ]
    assert packets[0]["packet"]["bilingual_display"] == packets[1]["packet"]["bilingual_display"]
    display = packets[0]["packet"]["bilingual_display"]
    assert display["semantic_reference_language"] == "en"
    assert display["reviewer_primary_display_language"] == "ja"
    assert "primary_reference_language" not in display
    assert packets[0]["packet"]["materials"]["question_text"] == reg.question.question_text
    serialized = json.dumps(packets[0]["packet"])
    assert "private-gold" not in serialized and "Invented final" not in serialized
    assert "AUTHOR-ONLY" not in serialized and "condition_mapping" not in serialized
    assert packets[0]["private_linkage"]["translation_asset_hash"] == asset.frozen_hash
    assert read(tmp_path / "r1/manifest.json")["bilingual_display_hash"]


def test_asset_and_text_tampering_rejected():
    value = artificial_asset(registry()).model_dump(mode="json")
    value["pairs"][0]["japanese_translation"] = "changed"
    with pytest.raises(ValidationError):
        TranslationAsset.model_validate(value)
    value["pairs"][0]["japanese_sha256"] = text_hash("changed")
    with pytest.raises(ValidationError):
        TranslationAsset.model_validate(value)  # Bundle hash still old.


def test_missing_rendering_wrong_version_and_reviewer_specific_asset_rejected(tmp_path):
    reg = registry()
    asset = artificial_asset(reg)
    flow = Workflow(reviewer_ids=("r1", "r2")).bind_translations(asset)
    value = asset.model_dump(mode="json", exclude={"frozen_hash"})
    value["version"] = "synthetic-ja-v2"
    other = TranslationAsset(**value, frozen_hash=digest(value))
    with pytest.raises(ValueError, match="same fixed translation"):
        build_packet(
            source(reg),
            flow,
            reg,
            "R1",
            "r2",
            tmp_path / "other",
            scope=scope(reg),
            translations=other,
        )
    value = asset.model_dump(mode="json", exclude={"frozen_hash"})
    value["pairs"] = value["pairs"][1:]
    missing = TranslationAsset(**value, frozen_hash=digest(value))
    fresh = Workflow(reviewer_ids=("r1", "r2")).bind_translations(missing)
    with pytest.raises(ValueError, match="Missing fixed Japanese rendering"):
        build_packet(
            source(reg),
            fresh,
            reg,
            "R1",
            "r1",
            tmp_path / "missing",
            scope=scope(reg),
            translations=missing,
        )


def test_cannot_replace_translation_after_binding_or_independent_locks():
    asset = artificial_asset(registry())
    flow = Workflow(reviewer_ids=("r1", "r2")).bind_translations(asset)
    with pytest.raises(ValueError):
        flow.bind_translations(asset)
    flow = Workflow(reviewer_ids=("r1", "r2")).lock("r1", "R1", {"synthetic": True}, "v1")
    with pytest.raises(ValueError):
        flow.bind_translations(asset)


def test_future_stage_translations_not_revealed_early(tmp_path):
    reg = registry()
    asset = artificial_asset(reg)
    # Bind before ANY independent ballot; use invented locks to test progressive stages.
    flow = Workflow(reviewer_ids=("synthetic-r1", "synthetic-r2"), synthetic=True)
    flow = flow.bind_translations(asset)
    prepared = workflow(reg)
    flow = prepared.model_copy(
        update={
            "translation_asset_hash": flow.translation_asset_hash,
            "translation_version": flow.translation_version,
        }
    )
    reg = frozen_registry(reg, flow)
    for phase in ("S1", "S2", "S3", "S4", "S5"):
        packet = build_packet(
            source(reg),
            flow,
            reg,
            phase,
            "synthetic-r1",
            tmp_path / phase,
            selected_arm="B",
            scope=scope(reg),
            translations=asset,
        )["packet"]
        pointers = [p["material_pointer"] for p in packet["bilingual_display"]["pairs"]]
        assert not any("benchmark_alignment" in p for p in pointers)
        assert any(p.startswith("/final_output") for p in pointers) == (phase == "S5")
        if phase == "S1":
            assert not any("public_output" in p or "supplementary_material" in p for p in pointers)
        assert all(f["annotation"]["state"] is None for f in packet["form"])
        flow = flow.lock("synthetic-r1", phase, {"artificial": phase}, "synthetic-v1")


def test_translation_ambiguity_is_separate_from_semantic_judgment():
    annotation = S2(
        question_id="invented",
        state="unclear",
        applicability="applicable",
        translation_issue="ambiguous",
        translation_unit_pointers=["/bilingual_display/0"],
        translation_visible_pairs_hash="synthetic-hash",
    )
    assert annotation.state == "unclear" and annotation.translation_issue == "ambiguous"
    # No automatic label generator: issue metadata alone leaves semantic state missing.
    assert S2(question_id="invented", translation_issue="mismatch").state is None
