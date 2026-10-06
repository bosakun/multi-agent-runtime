"""Wholly invented sources/translations for visual and mechanical examples only."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from review_v3.bilingual import text_hash  # noqa: E402
from review_v3.html_display_v1.renderer import build  # noqa: E402
from review_v3.storage import digest, exclusive  # noqa: E402


def synthetic_a():
    r1 = dict(
        case_alias="SYNTHETIC-DEMO-01",
        question="Where is the fictional Elm Archive? (Synthetic demonstration.)",
        reference_sentences=[
            dict(
                sentence_id="demo-s1",
                title="Fictional Elm Archive",
                sentence_index=0,
                sentence_text="The fictional Elm Archive is in Pine Town.",
            )
        ],
    )
    r2 = {
        **r1,
        "benchmark_alignment": dict(
            gold_answer="Pine Town", gold_supporting_facts=[["Fictional Elm Archive", 0]]
        ),
    }
    texts = [
        ("/question", r1["question"], "架空のニレ資料館はどこにありますか。（人工の表示例です。）"),
        ("/reference_sentences/0/title", "Fictional Elm Archive", "架空のニレ資料館"),
        (
            "/reference_sentences/0/sentence_text",
            r1["reference_sentences"][0]["sentence_text"],
            "架空のニレ資料館はマツの町にあります。",
        ),
        ("/benchmark_alignment/gold_answer", "Pine Town", "マツの町"),
        (
            "/benchmark_alignment/gold_supporting_facts/0/0",
            "Fictional Elm Archive",
            "架空のニレ資料館",
        ),
    ]
    pairs = [
        dict(
            english_original=en,
            japanese_translation=ja,
            english_sha256=text_hash(en),
            japanese_sha256=text_hash(ja),
            source_pointers=["synthetic_fixture:" + pointer],
            display_pointers=[pointer],
        )
        for pointer, en, ja in texts
    ]
    asset = dict(
        version="synthetic-display-example-v1",
        review_mode="pilot",
        question_id=r1["case_alias"],
        pairs=pairs,
        preparation_method="wholly invented example",
        translation_method="other",
        translation_prepared_by_or_system="synthetic fixture",
        translation_verified_by="SYNTHETIC TEST ONLY — no real verifier",
        verification_method="synthetic fixture hash checks only",
        translation_system_metadata={},
        human_approved_by="SYNTHETIC TEST ONLY — no human signoff",
        frozen_at="2000-01-01T00:00:00Z",
    )
    asset["frozen_hash"] = digest(asset)
    return r1, r2, asset


def synthetic_b(phase):
    from review_v3.pilot_materials_v1.prepare import MARKER

    pair = dict(
        en="The fictional Elm Archive is in Pine Town.", ja="架空のニレ資料館はマツの町にあります。"
    )
    value = dict(
        marker=MARKER,
        vignette_id="SYNTHETIC-PB-DEMO",
        phase=phase,
        question=dict(
            en="Where is the fictional Elm Archive?", ja="架空のニレ資料館はどこですか。"
        ),
        reference=[dict(sentence_id="s1", text=pair)],
        teaching_reference=dict(
            marker="SYNTHETIC TEACHING PREMISES; NOT A REAL FACT REGISTRY",
            facts=[dict(fact_id="f1", text=pair)],
            support_sets=[dict(support_set_id="ss1", fact_id="f1", evidence_sentence_ids=["s1"])],
            paths=[dict(path_id="p1", required_fact_ids=["f1"], support_set_ids=["ss1"])],
        ),
        actual_worker_input_sentence_ids={"w1": ["s1"]},
        exercise_prompt_ja="人工資料を使って、この段階の表示を確認してください。",
    )
    if phase != "S1":
        value["worker_public_expression"] = {"w1": pair}
    if phase in {"S3", "S4", "S5"}:
        value.update(publication_transition_type="identity_alias", published_artifact={"w1": pair})
    if phase in {"S4", "S5"}:
        value["actual_synthesizer_input"] = dict(artifacts={"w1": pair}, supplementary_evidence=[])
    if phase == "S5":
        value["final_output"] = dict(en="Pine Town", ja="マツの町")
    return value


def prepare_examples(root):
    root = Path(root)
    if root.exists():
        raise ValueError("Fresh synthetic example directory required")
    r1, r2, asset = synthetic_a()
    exclusive(root / "synthetic-fixed-translation.json", asset)
    for phase, source in [("R1", r1), ("R2", r2)]:
        path = root / (phase + ".synthetic.json")
        exclusive(path, source)
        build(path, phase, root / phase, root / "synthetic-fixed-translation.json")
    for phase in ("S1", "S2", "S3", "S4", "S5"):
        path = root / (phase + ".synthetic.json")
        exclusive(path, synthetic_b(phase))
        build(path, phase, root / phase)


if __name__ == "__main__":
    prepare_examples(sys.argv[1])
    print("Synthetic examples prepared; no real translation/review/signoff")
