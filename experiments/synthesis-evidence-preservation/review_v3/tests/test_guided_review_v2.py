"""Guided UI v2 checks use only wholly artificial sources and existing schemas."""

import copy
import json
from typing import get_args

import pytest
from review_v3.html_display_v1.examples import synthetic_a, synthetic_b
from review_v3.html_review_v2.audit import verify
from review_v3.html_review_v2.renderer import (
    CODEBOOK_VERSION,
    LABELS,
    build,
    index_html,
    make_stage_ballot,
    normalize_a,
    normalize_b,
    page_html,
    validate_export,
)
from review_v3.schema import STAGE_MODELS
from review_v3.storage import exclusive, file_hash


def scripts(page):
    text = page.decode("utf-8")
    values = []
    rest = text
    while "<script>" in rest:
        rest = rest.split("<script>", 1)[1]
        script, rest = rest.split("</script>", 1)
        values.append(script)
    return text, values


def test_label_display_does_not_change_canonical_states():
    assert LABELS["correct"] == "正しく残っている"
    assert LABELS["partial"] == "一部だけある：関係する内容はあるが、この事実までは判断できない"
    assert LABELS["distorted"] == "情報はあるが、重要な内容が変わっている"
    assert LABELS["absent"] == "ない：この事実に当たる内容は書かれていない"
    assert LABELS["unclear"] == "判断できない：文章が曖昧などの理由で決められない"
    assert {
        value
        for value in get_args(get_args(STAGE_MODELS["S2"].model_fields["state"].annotation)[0])
    } == {"correct", "partial", "distorted", "absent", "unclear", "NA"}


@pytest.mark.parametrize("phase", ["S1", "S2", "S3", "S4", "S5"])
def test_synthetic_tutorial_is_phase_limited_and_guided(phase):
    case = normalize_b(synthetic_b(phase), phase)
    page = page_html([case], phase, "source-hash")
    text, js = scripts(page)
    assert "今回確認すること" in text
    assert "① 今回確認する事実" in text
    assert "② 実際の文章" in text
    assert "③ あなたの判定" in text
    assert "この段階ではまだ見ないもの" in text
    assert "英語原文を確認" in text
    assert "SYNTHETIC CALIBRATION MATERIAL" in text
    assert "NOT STUDY DATA" in text and "NOT MODEL OUTPUT" in text
    assert "author_key" not in text and "intended_label" not in text
    assert len(js) == 1
    assert "answer_key" not in js[0] and "intended_label" not in js[0]
    assert "comment" not in text.lower()
    if phase == "S1":
        assert "worker_public_expression" not in text
        assert "PRIVATE_S2_SENTINEL" not in text
    if phase != "S5":
        assert "The final answer is Pine Town." not in text


def test_r1_and_r2_render_phase_separately_and_keep_english():
    r1, r2, asset = synthetic_a()
    one = normalize_a(r1, "R1", asset, "a" * 64)
    two = normalize_a(r2, "R2", asset, "b" * 64)
    r1_page, _ = scripts(page_html([one], "R1", "r1-key"))
    r2_page, r2_js = scripts(page_html([two], "R2", "r2-key"))
    r1_data = json.loads(
        r1_page.split('<script id="review-data" type="application/json">', 1)[1].split(
            "</script>", 1
        )[0]
    )
    assert r1_data["cases"][0]["gold"] is None
    assert "The final answer is Pine Town." not in r1_page
    assert "Gold情報（R2）" in r2_page and "Pine Town" in r2_page
    assert "Worker Output" not in r2_page and "S5 · 最終出力" not in r2_page
    assert "英語原文を確認" in r1_page and "meaning" not in r1_page


def test_r1_inline_data_has_no_future_translation_or_private_source_pointer():
    r1, r2, asset = synthetic_a()
    asset = copy.deepcopy(asset)
    asset["pairs"].append(
        {
            "english_original": "PRIVATE_S2_SENTINEL",
            "japanese_translation": "S2秘密",
            "english_sha256": "",
            "japanese_sha256": "",
            "source_pointers": ["private"],
            "display_pointers": ["/future"],
        }
    )
    from review_v3.bilingual import text_hash
    from review_v3.storage import digest

    asset["pairs"][-1]["english_sha256"] = text_hash("PRIVATE_S2_SENTINEL")
    asset["pairs"][-1]["japanese_sha256"] = text_hash("S2秘密")
    asset["frozen_hash"] = digest({k: v for k, v in asset.items() if k != "frozen_hash"})
    case = normalize_a(r1, "R1", asset, "c" * 64)
    text, js = scripts(page_html([case], "R1", "r1-key"))
    assert "PRIVATE_S2_SENTINEL" not in text
    assert "/reference_sentences/0/sentence_text" not in text
    data = json.loads(
        text.split('<script id="review-data" type="application/json">', 1)[1].split("</script>", 1)[
            0
        ]
    )
    assert "translation_map_hash" not in data["cases"][0]
    assert "translation_hash" not in data["cases"][0]
    assert "PRIVATE_S2_SENTINEL" not in js[0]


def test_answer_key_fields_are_rejected_before_rendering():
    case = synthetic_b("S1")
    case["author_key"] = "KEY_SENTINEL"
    with pytest.raises(ValueError):
        normalize_b(case, "S1")
    case = synthetic_b("S1")
    case["teaching_reference"]["facts"][0]["intended_label"] = "correct"
    with pytest.raises(ValueError):
        normalize_b(case, "S1")


def test_existing_stage_ballot_export_validates_and_keeps_source_separate():
    source = synthetic_b("S1")
    before = copy.deepcopy(source)
    case = normalize_b(source, "S1")
    selections = ["complete"] * len(case["form"])
    ballot = make_stage_ballot(case["form"], selections, {}, "pilot-reviewer-1", {"0": ["s1"]})
    assert validate_export(ballot, "S1")
    assert source == before
    assert ballot[0]["annotation"]["state"] == "complete"
    assert ballot[0]["annotation"]["reviewer_id"] == "pilot-reviewer-1"
    assert ballot[0]["annotation"]["codebook_version"] == CODEBOOK_VERSION
    with pytest.raises(ValueError, match="unclear"):
        make_stage_ballot(case["form"], ["unclear"] * len(case["form"]), {}, "reviewer")


def test_identity_alias_ballot_uses_existing_na_rule():
    case = normalize_b(synthetic_b("S3"), "S3")
    ballot = make_stage_ballot(case["form"], ["NA"] * len(case["form"]), {}, "reviewer")
    assert validate_export(ballot, "S3")
    assert ballot[0]["annotation"]["applicability"] == "not_applicable"
    assert ballot[0]["annotation"]["applicability_reason"] == "no_separate_transition"


def test_s5_exports_two_existing_label_models():
    case = normalize_b(synthetic_b("S5"), "S5")
    selections = [
        "reflected" if row["stage"] == "S5a" else "fully_supported" for row in case["form"]
    ]
    ballot = make_stage_ballot(case["form"], selections, {}, "reviewer")
    assert [row["stage"] for row in ballot] == ["S5a", "S5b"]
    assert validate_export(ballot, "S5")


def test_s4_route_uses_existing_canonical_field_with_japanese_display():
    case = normalize_b(synthetic_b("S4"), "S4")
    selections = ["correct"] * len(case["form"])
    routes = {str(i): "supplementary_evidence" for i in range(len(case["form"]))}
    ballot = make_stage_ballot(case["form"], selections, {}, "reviewer", routes=routes)
    assert validate_export(ballot, "S4")
    assert all(row["annotation"]["received_via"] == "supplementary_evidence" for row in ballot)
    page = page_html([case], "S4", "a" * 64).decode()
    assert "追加資料として" in page


def test_registry_export_uses_canonical_registry_object():
    r1, _, asset = synthetic_a()
    case = normalize_a(r1, "R1", asset, "d" * 64)
    registry = case["registry"]
    registry["facts"] = [
        {
            "fact_id": "F1",
            "fact_text": "事実",
            "fact_type": "atomic_fact",
            "reference_basis": "raw_discovery",
        }
    ]
    registry["support_sets"] = [
        {
            "support_set_id": "SS1",
            "fact_id": "F1",
            "evidence_sentence_ids": [registry["sentences"][0]["sentence_id"]],
            "support_set_sufficient": "yes",
        }
    ]
    registry["paths"] = [
        {
            "path_id": "P1",
            "path_basis": "raw_discovered_alternative",
            "target_answer": "回答",
            "validity": "yes",
        }
    ]
    registry["memberships"] = [
        {
            "question_id": registry["question"]["question_id"],
            "path_id": "P1",
            "fact_id": "F1",
            "required_within_path": "yes",
            "support_set_ids": ["SS1"],
        }
    ]
    assert validate_export({"registry": registry, "provenance": {}}, "R1")


def test_phase_bundle_deterministic_manifest_and_pointer_hashes(tmp_path):
    source = tmp_path / "S5.synthetic.json"
    exclusive(source, [synthetic_b("S5")])
    first_dir, second_dir = tmp_path / "bundle-one", tmp_path / "bundle-two"
    first = build(source, "S5", first_dir)
    second = build(source, "S5", second_dir)
    assert first["renderer_source_hash"] == second["renderer_source_hash"]
    for filename, sha in first["html_sha256"].items():
        assert file_hash(first_dir / filename) == sha
        assert (first_dir / filename).read_bytes() == (second_dir / filename).read_bytes()
    assert first["text_lineage_by_case"] == second["text_lineage_by_case"]
    assert first["phase"] == "S5" and first["human_review_started"] is False
    assert verify(first_dir)["valid"] is True
    (first_dir / "review.html").write_bytes(b"tampered")
    assert verify(first_dir)["valid"] is False


def test_index_explains_task_and_lists_alias_progress():
    case = normalize_b(synthetic_b("S1"), "S1")
    page = index_html([case], "S1", "a" * 64).decode()
    assert "今回すること" in page and "比較するもの" in page and "回答する質問" in page
    assert "Case 1 / 1" in page and "PB-" in page
    assert "reviewer-id" in page and "Reviewを開始する" in page


def test_overview_and_review_data_do_not_modify_canonical_source():
    source = synthetic_b("S2")
    before = copy.deepcopy(source)
    case = normalize_b(source, "S2")
    page, _ = scripts(page_html([case], "S2", "b" * 64))
    assert "そのAIが他のAIに伝えた文章" in page
    assert source == before
