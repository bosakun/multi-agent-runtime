"""Synthetic display checks; no real translation/semantic labels/review performed."""

import copy
import html
from pathlib import Path

import pytest
from review_v3.bilingual import TranslationAsset, bilingual_projection, display_texts, text_hash
from review_v3.html_display_v1.audit import verify
from review_v3.html_display_v1.examples import synthetic_a, synthetic_b
from review_v3.html_display_v1.renderer import build, pointer_get, render, renderer_hash
from review_v3.schema import Question, Registry, Sentence
from review_v3.storage import digest, exclusive, file_hash, read


def refresh(asset):
    asset["frozen_hash"] = digest({k: v for k, v in asset.items() if k != "frozen_hash"})
    return asset


def test_r1_has_no_future_data_even_with_full_translation_asset():
    r1, _, asset = synthetic_a()
    asset["pairs"][3]["english_original"] = "SECRET_GOLD_FUTURE"
    asset["pairs"][3]["english_sha256"] = text_hash("SECRET_GOLD_FUTURE")
    output = render(r1, "R1", refresh(asset))[1].decode()
    assert "SECRET_GOLD_FUTURE" not in output
    assert "Gold Supporting Facts" not in output
    assert "Worker公開出力" not in output and "実Synthesizer入力" not in output
    assert "S5 · 最終出力" not in output
    assert "この段階ではGold Answer、Worker Output、Final Answer等は参照しない" in output


def test_r2_gold_but_no_system_outputs():
    _, r2, asset = synthetic_a()
    output = render(r2, "R2", asset)[1].decode()
    assert "Gold Answer · benchmark alignment" in output and "Gold Supporting Facts" in output
    assert "Pine Town" in output and "マツの町" in output
    assert "Worker公開出力" not in output and "実Synthesizer入力" not in output
    assert "S5 · 最終出力" not in output


@pytest.mark.parametrize(
    "field",
    ["benchmark_alignment", "worker_output", "artifact", "final_output", "score", "condition"],
)
def test_prepared_r1_rejects_future_fields(field):
    r1, _, asset = synthetic_a()
    r1[field] = "DO_NOT_EXPORT_SECRET"
    with pytest.raises(ValueError):
        render(r1, "R1", asset)


@pytest.mark.parametrize("phase", ["S1", "S2", "S3", "S4", "S5"])
def test_b_stage_physical_separation(phase):
    source = synthetic_b(phase)
    output = render(source, phase)[1].decode()
    assert "SYNTHETIC CALIBRATION MATERIAL" in output
    assert "NOT STUDY DATA" in output and "NOT MODEL OUTPUT" in output
    assert ("S2 · Worker public expression" in output) == (phase != "S1")
    assert ("S3 · 公開Artifact" in output) == (phase in {"S3", "S4", "S5"})
    assert ("S4 · 実Synthesizer入力" in output) == (phase in {"S4", "S5"})
    assert ("S5 · 最終出力" in output) == (phase == "S5")
    assert "<script" not in output and "<!--" not in output and "data-" not in output


@pytest.mark.parametrize(
    "field",
    [
        "worker_public_expression",
        "published_artifact",
        "actual_synthesizer_input",
        "final_output",
        "author_key",
    ],
)
def test_s1_rejects_future_and_key(field):
    source = synthetic_b("S1")
    source[field] = "SECRET_FUTURE"
    with pytest.raises(ValueError):
        render(source, "S1")


def test_nested_answer_key_rejected():
    source = synthetic_b("S4")
    source["actual_synthesizer_input"]["answer_key"] = "SECRET_AUTHOR_KEY"
    with pytest.raises(ValueError):
        render(source, "S4")
    source = synthetic_b("S1")
    source["teaching_reference"]["facts"][0]["intended_label"] = "correct"
    with pytest.raises(ValueError):
        render(source, "S1")
    source = synthetic_b("S1")
    source["actual_worker_input_sentence_ids"]["w1"] = {"answer_key": "secret"}
    with pytest.raises(ValueError):
        render(source, "S1")


def test_no_translation_generation_and_hash_validation():
    r1, _, asset = synthetic_a()
    with pytest.raises(ValueError):
        render(r1, "R1")
    asset["pairs"][0]["japanese_translation"] = "changed"
    with pytest.raises(ValueError):
        render(r1, "R1", asset)


def test_text_hash_and_pointer_alignment():
    r1, _, asset = synthetic_a()
    _, output, lineage, _ = render(r1, "R1", asset)
    for row in lineage:
        assert row["english_sha256"] == text_hash(pointer_get(r1, row["source_pointer"]))
        i = int(row["translation_pointer"].split("/")[2])
        ja = asset["pairs"][i]["japanese_translation"]
        assert text_hash(ja) == row["japanese_sha256"]
        assert html.escape(ja).encode() in output


def test_script_escape_and_no_external_dependencies():
    source = synthetic_b("S1")
    original = '<script>alert("PRIVATE")</script> & <img src="https://invalid.example">'
    source["question"]["en"] = original
    source["question"]["ja"] = "人工のescape確認"
    output = render(source, "S1")[1].decode()
    assert html.escape(original) in output
    assert "<script" not in output and "<img" not in output
    assert "<link" not in output and "<iframe" not in output


def test_deterministic_bundle_manifest_and_no_overwrite(tmp_path):
    source = tmp_path / "source.json"
    exclusive(source, [synthetic_b("S1")])
    first = build(source, "S1", tmp_path / "one")
    second = build(source, "S1", tmp_path / "two")
    assert first == second
    assert verify(tmp_path / "one")["passed"]
    assert first["renderer_source_hash"] == renderer_hash()
    for entry in first["entries"]:
        assert file_hash(tmp_path / "one" / entry["html_file"]) == entry["html_sha256"]
        assert (tmp_path / "one" / entry["html_file"]).read_bytes() == (
            tmp_path / "two" / entry["html_file"]
        ).read_bytes()
        for pair in entry["text_lineage"]:
            assert (
                text_hash(pointer_get(read(source), pair["source_pointer"]))
                == pair["english_sha256"]
            )
            assert (
                text_hash(pointer_get(read(source), pair["translation_pointer"]))
                == pair["japanese_sha256"]
            )
    assert file_hash(tmp_path / "one/index.html") == first["index_html_sha256"]
    before = file_hash(tmp_path / "one/render-manifest.json")
    with pytest.raises(ValueError):
        build(source, "S1", tmp_path / "one")
    assert file_hash(tmp_path / "one/render-manifest.json") == before


def test_failed_bundle_does_not_create_directory(tmp_path):
    bad = synthetic_b("S1")
    bad["final_output"] = "SECRET"
    exclusive(tmp_path / "bad.json", [synthetic_b("S1"), bad])
    with pytest.raises(ValueError):
        build(tmp_path / "bad.json", "S1", tmp_path / "out")
    assert not (tmp_path / "out").exists()


def packet_fixture():
    r1, _, asset = synthetic_a()
    materials = dict(
        question_text=r1["question"],
        reference_sentences=[
            Sentence(
                sentence_id=s["sentence_id"],
                title=s["title"],
                sentence_index=s["sentence_index"],
                text=s["sentence_text"],
                text_hash=text_hash(s["sentence_text"]),
            ).model_dump()
            for s in r1["reference_sentences"]
        ],
    )
    for pair in asset["pairs"]:
        pair["display_pointers"] = [
            p.replace("/question", "/question_text").replace("/sentence_text", "/text")
            for p in pair["display_pointers"]
        ]
    refresh(asset)
    packet = dict(
        case_code=r1["case_alias"],
        phase="R1",
        review_mode="pilot",
        materials=materials,
        bilingual_display=bilingual_projection(materials, TranslationAsset.model_validate(asset)),
    )
    return packet, asset


def test_existing_canonical_packet_supported():
    packet, asset = packet_fixture()
    output = render(packet, "R1", asset)[1]
    assert "架空のニレ資料館".encode() in output
    packet["bilingual_display"]["pairs"].append(asset["pairs"][3])
    with pytest.raises(ValueError):
        render(packet, "R1", asset)


def test_canonical_s1_rejects_s2_worker_field():
    packet, asset = packet_fixture()
    packet["phase"] = "S1"
    materials = packet["materials"]
    materials.update(
        registry_projection=Registry(
            question=Question(
                question_id=packet["case_code"],
                question_text=materials["question_text"],
                source_hash="synthetic",
                registry_version="synthetic-only",
            )
        ).model_dump(),
        workers=[
            dict(
                worker="worker-1",
                actual_input_available=True,
                actual_input_sentences=[],
                public_output={"text": "SECRET_S2"},
            )
        ],
    )
    with pytest.raises(ValueError):
        render(packet, "S1", asset)


def test_r2_personal_r1_not_in_shared_html():
    packet, asset = packet_fixture()
    _, r2, _ = synthetic_a()
    packet["phase"] = "R2"
    packet["materials"]["benchmark_alignment"] = r2["benchmark_alignment"]
    own = Registry(
        question=Question(
            question_id=packet["case_code"],
            question_text="PERSONAL_R1_A",
            source_hash="synthetic",
            registry_version="synthetic-only",
        )
    ).model_dump()
    packet["materials"]["own_locked_R1_registry"] = own
    packet["bilingual_display"] = bilingual_projection(
        packet["materials"], TranslationAsset.model_validate(asset)
    )
    first = render(packet, "R2", asset)[1]
    own["question"]["question_text"] = "PERSONAL_R1_B"
    second = render(packet, "R2", asset)[1]
    assert first == second and b"PERSONAL_R1_A" not in first and b"PERSONAL_R1_B" not in second


@pytest.mark.parametrize("phase", ["S1", "S2", "S3", "S4", "S5"])
def test_canonical_valid_stage_and_metadata(phase):
    packet, asset = packet_fixture()
    packet["phase"] = phase
    materials = packet["materials"]
    materials["registry_projection"] = Registry(
        question=Question(
            question_id=packet["case_code"],
            question_text=materials["question_text"],
            source_hash="synthetic",
            registry_version="synthetic-only",
        )
    ).model_dump()
    worker = dict(
        worker="worker-1",
        actual_input_available=True,
        actual_input_sentences=materials["reference_sentences"],
    )
    if phase != "S1":
        worker["public_output"] = dict(
            text="SYNTHETIC_WORKER_TEXT", evidence_ids=["demo-s1"], level="low"
        )
    if phase in {"S3", "S4", "S5"}:
        worker.update(
            publication_transition_type="identity_alias",
            public_artifact={"text": "SYNTHETIC_ARTIFACT_TEXT"},
        )
    materials["workers"] = [worker]
    if phase in {"S4", "S5"}:
        materials["actual_synthesizer_input"] = dict(
            artifacts=[dict(producer="worker-1", payload={"text": "SYNTHETIC_RECEIVED_TEXT"})],
            supplementary_material="SYNTHETIC_SUPPLEMENT",
        )
    if phase == "S5":
        materials["final_output"] = {"answer": "SYNTHETIC_FINAL_TEXT"}
    originals = {p["english_original"]: p["japanese_translation"] for p in asset["pairs"]}
    originals.update(
        SYNTHETIC_WORKER_TEXT="人工のWorker文章",
        SYNTHETIC_ARTIFACT_TEXT="人工Artifact文章",
        SYNTHETIC_RECEIVED_TEXT="人工の受信文章",
        SYNTHETIC_SUPPLEMENT="人工の追加文章",
        SYNTHETIC_FINAL_TEXT="人工の最終文章",
    )
    asset["pairs"] = [
        dict(
            english_original=en,
            japanese_translation=originals[en],
            english_sha256=text_hash(en),
            japanese_sha256=text_hash(originals[en]),
            source_pointers=["synthetic:" + ptr],
            display_pointers=[ptr],
        )
        for ptr, en in display_texts(materials)
    ]
    refresh(asset)
    packet["bilingual_display"] = bilingual_projection(
        materials, TranslationAsset.model_validate(asset)
    )
    output = render(packet, phase, asset)[1].decode()
    assert ("SYNTHETIC_WORKER_TEXT" in output) == (phase != "S1")
    assert ("SYNTHETIC_FINAL_TEXT" in output) == (phase == "S5")
    assert ("SYNTHETIC_SUPPLEMENT" in output) == (phase in {"S4", "S5"})


def test_source_not_mutated_by_renderer():
    source = synthetic_b("S5")
    before = copy.deepcopy(source)
    a = render(source, "S5")[1]
    b = render(source, "S5")[1]
    assert source == before and a == b


def test_selected_ids_static_source_unchanged():
    path = Path(__file__).resolve().parents[1] / "pilot_materials_v1/pilot_materials_manifest.json"
    manifest = read(path)
    assert manifest["pilot_a"]["selected_ids"] == [
        "5adddb415542992200553b61",
        "5a74c2bd5542996c70cfadda",
        "5ab431d855429942dd415ed2",
        "5a865cac55429960ec39b675",
        "5a7ed2c655429930675135e5",
        "5ae5064e5542993aec5ec113",
    ]
