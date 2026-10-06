"""Build a guided, deterministic, phase-limited local review UI from v3 JSON."""

# Embedded HTML, JavaScript, and Japanese interface copy intentionally use long literals.
# ruff: noqa: E501

import argparse
import hashlib
import html
import json
import sys
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from review_v3 import SCHEMA_VERSION  # noqa: E402
from review_v3.bilingual import TranslationAsset, bilingual_projection, text_hash  # noqa: E402
from review_v3.codebook import CANDIDATE_VERSION as CODEBOOK_VERSION  # noqa: E402
from review_v3.html_display_v1 import renderer as v1  # noqa: E402
from review_v3.html_review_v2 import VERSION  # noqa: E402
from review_v3.pilot_materials_v1.prepare import MARKER  # noqa: E402
from review_v3.schema import STAGE_MODELS, Registry  # noqa: E402
from review_v3.storage import (  # noqa: E402
    digest,
    ensure_local_output,
    exclusive,
    file_hash,
    read,
)

HERE = Path(__file__).resolve().parent
PHASES = ("R1", "R2", "S1", "S2", "S3", "S4", "S5")

GUIDE = {
    "R1": dict(
        title="事実と証拠の道筋を整理する",
        purpose="回答に必要な事実が、どの証拠文から分かるかを整理します。",
        see="質問と参考文書（Raw Evidence）",
        compare="質問で求められることと、参考文書に書かれたこと",
        answer="どの事実が必要で、どの文がそれを支えるか。事実・証拠文の組・回答までの道筋を記録してください。",
        avoid="Gold Answer、Gold Supporting Facts、Workerや最終回答など後の段階の資料",
        action="英語原文を意味の基準として、事実・証拠文の組・道筋を記録してください。",
    ),
    "R2": dict(
        title="正解情報と自分の候補を照らす",
        purpose="R1で自分が整理した候補を、ベンチマークの正解情報（Gold）と照らして確認・調整します。",
        see="質問、参考文書、Gold Answer、Gold Supporting Facts、自分が固定したR1候補",
        compare="自分のR1候補とベンチマークの正解情報",
        answer="候補を維持・修正すべきか。各道筋が妥当か、その道筋内で必要な事実は何か。",
        avoid="Worker出力、共有Artifact、Synthesizer入力、最終回答、条件名やscore",
        action="自分のR1候補を確認し、必要な修正をRegistryへ記録してください。",
    ),
    "S1": dict(
        title="Workerに必要な情報が届いたか",
        purpose="必要な証拠文が、対象Workerの実際の入力に含まれていたかを確認します。",
        see="固定済みの必要情報一覧、参考文書、対象Workerの実際の入力",
        compare="必要な情報を支える証拠文と、Worker入力に記録された文",
        answer="必要な証拠はこのWorkerの入力にどの程度含まれていましたか。",
        avoid="Workerが他Agentに公開した文章、Artifact、Synthesizer入力、最終回答",
        action="実際の入力記録と必要な証拠を比べ、該当する状態を選んでください。",
    ),
    "S2": dict(
        title="必要な情報がWorkerの公開文章に残ったか",
        purpose="Workerが他のAgentに公開した文章に、必要な情報が意味として残っているかを確認します。",
        see="必要な事実、参考文書、Workerの実際の入力、Workerが他Agentに公開した文章（Worker Public Expression）",
        compare="必要な事実と、実際のWorker公開文章",
        answer="回答に必要な情報が、Workerの公開文章に正しく残っていますか。",
        avoid="共有Artifact以降の記録、Synthesizer入力、最終回答",
        action="回答に必要な情報が、Workerの公開文章に正しく残っているか確認してください。",
    ),
    "S3": dict(
        title="共有Artifactへの移行で情報が変わったか",
        purpose="Workerが他Agentに公開した文章と、後段へ共有された記録（Artifact）を比べます。",
        see="必要な事実、Worker公開文章、共有前後の記録（Publication Transition / Artifact）",
        compare="Worker公開文章と、共有Artifact",
        answer="独立したArtifact作成段階で、情報が保持・一部欠落・変形・消失しましたか。",
        avoid="Synthesizer入力、最終回答",
        action="公開文章とArtifactを比べ、遷移の種類に沿って状態を選んでください。",
    ),
    "S4": dict(
        title="情報が最終回答を作るAgentへ届いたか",
        purpose="最終回答を作るAgent（Synthesizer）の実際の入力に、必要な情報がどの経路で含まれているかを確認します。",
        see="必要な事実、Worker公開文章、共有Artifact、Synthesizerの実際の入力",
        compare="必要な事実と、Synthesizer入力にある各経路の情報",
        answer="必要な情報はSynthesizer入力に正しく含まれていますか。どの経路で届きましたか。",
        avoid="最終回答",
        action="Artifact経路と追加資料の経路を区別し、実際に届いた情報を判定してください。",
    ),
    "S5": dict(
        title="届いた証拠で最終回答を支持できるか",
        purpose="Synthesizer入力に届いた証拠で、最終回答を支持できるかを確認します。",
        see="固定済みの必要情報、S4で実際に届いた情報、最終回答",
        compare="受け取った証拠の道筋と、最終回答",
        answer="最終回答は、S4で利用可能だった完全な道筋で十分に支持できますか。事実を述べたかどうかも別々に記録してください。",
        avoid="他の条件の回答、集計score、仮説への適合",
        action="事実との関係と、受信済み証拠による支持を分けて判定してください。",
    ),
}

LABELS = {
    "complete": "ある：この事実を判断できる内容が書かれている",
    "partial": "一部だけある：関係する内容はあるが、この事実までは判断できない",
    "absent": "ない：この事実に当たる内容は書かれていない",
    "unclear": "判断できない：文章が曖昧などの理由で決められない",
    "none": "ない：この事実を判断できる内容は書かれていない",
    "correct": "正しく残っている",
    "distorted": "情報はあるが、重要な内容が変わっている",
    "NA": "構造上、この段階は該当しない",
    "retained": "情報が保たれている",
    "partial_loss": "一部の情報が失われている",
    "lost": "情報が失われている",
    "fully_supported": "言える：届いた証拠から、この回答を十分に支持できる",
    "partially_supported": "一部は支持できるが、十分ではない",
    "unsupported": "言えない：届いた証拠から、この回答を支持できない",
    "reflected": "最終出力に事実が表れている",
    "contradicted": "最終出力が事実と矛盾している",
    "not_asserted": "最終出力ではこの事実を述べていない",
}

# Presentation only: canonical stage states and annotation units remain unchanged.
for _stage, _title, _record, _why, _avoid in (
    (
        "S1",
        "この事実は、最初のAIが読んだ資料に書かれていたか",
        "最初のAIが実際に読んだ文章",
        "資料にこの事実がなければ、後の回答へ伝えられない可能性があります。",
        "AIが他のAIに伝えた文章、共有後の情報、最後のAIの資料、最終回答",
    ),
    (
        "S2",
        "この事実は、AIが他のAIに伝えた文章に残っていたか",
        "そのAIが他のAIに伝えた文章",
        "資料に書かれていても、伝える文章から消えることがあります。",
        "共有後の情報、最後のAIの資料、最終回答",
    ),
    (
        "S3",
        "この事実は、共有用のデータに移った後も残っていたか",
        "共有する前の文章と、共有用のデータに移った後の文章",
        "共有する前後で、文章の意味が変わっていないかを確認します。",
        "最後のAIの資料、最終回答",
    ),
    (
        "S4",
        "この事実は、最後に回答を作るAIが読んだ資料に入っていたか",
        "最後に回答を作るAIが実際に読んだ文章",
        "途中にあった事実でも、最後のAIまで届かないことがあります。",
        "最終回答",
    ),
    (
        "S5",
        "最終回答はこの事実と矛盾していないか／届いた証拠から回答を支持できるか",
        "最後のAIが読んだ文章と最終回答",
        "正しい答えかどうかだけでなく、届いた証拠でその回答を言えるかを確認します。",
        "他の条件の回答、点数、研究結果",
    ),
):
    GUIDE[_stage].update(
        title=_title,
        purpose=_why,
        see=_record,
        compare="画面に示す確認対象と、実際の文章",
        answer=_title,
        avoid=_avoid,
        action="示された事実と文章を比べ、下の日本語の選択肢から選んでください。",
    )

STAGE_FORMS = {"S1": ("S1",), "S2": ("S2",), "S3": ("S3",), "S4": ("S4",), "S5": ("S5a", "S5b")}


def esc(value):
    return html.escape(str(value), quote=True)


def js_json(value):
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def pair_for(pointer, english, translation_map):
    if not isinstance(english, str):
        raise ValueError("Expected stage-authorized English source text")
    pair = translation_map.get(pointer)
    if pair is None or pair["english_original"] != english:
        raise ValueError(f"Missing matching fixed Japanese translation: {pointer}")
    return {
        "ja": pair["japanese_translation"],
        "en": english,
        "pointer": pointer,
        "en_hash": text_hash(english),
        "ja_hash": pair["japanese_sha256"],
    }


def localize_tree(value, pointer, translation_map):
    if isinstance(value, str):
        pair = translation_map.get(pointer)
        if pair and pair["english_original"] == value:
            return pair_for(pointer, value, translation_map)
        return {"ja": value, "en": "", "pointer": pointer, "en_hash": "", "ja_hash": ""}
    if isinstance(value, list):
        return [
            localize_tree(item, f"{pointer}/{i}", translation_map) for i, item in enumerate(value)
        ]
    if isinstance(value, dict):
        return {
            key: localize_tree(item, f"{pointer}/{key}", translation_map)
            for key, item in value.items()
        }
    return value


def text_lineage(value, pointer=""):
    rows = []
    if isinstance(value, dict):
        if {"pointer", "en_hash", "ja_hash"} <= value.keys():
            rows.append(
                {
                    "source_pointer": value["pointer"],
                    "english_sha256": value["en_hash"],
                    "japanese_sha256": value["ja_hash"],
                }
            )
        else:
            for key, item in value.items():
                rows.extend(text_lineage(item, pointer + "/" + str(key)))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            rows.extend(text_lineage(item, pointer + "/" + str(i)))
    return rows


def reviewer_projection(value):
    """Keep review prose while moving hashes, pointers, and provenance to the manifest."""
    if isinstance(value, dict):
        if {"ja", "en", "pointer", "en_hash", "ja_hash"} <= value.keys():
            return {"ja": value["ja"], "en": value["en"]}
        return {
            key: reviewer_projection(item)
            for key, item in value.items()
            if key not in {"translation_hash", "translation_map_hash"}
        }
    if isinstance(value, list):
        return [reviewer_projection(item) for item in value]
    return value


def synthetic_pair(value, pointer):
    v1.check_bilingual(value)
    return {
        "ja": value["ja"],
        "en": value["en"],
        "pointer": pointer,
        "en_hash": text_hash(value["en"]),
        "ja_hash": text_hash(value["ja"]),
    }


def make_registry_form(question_id, question_text, source_hash, sentences, seed=None):
    if seed is not None:
        return Registry.model_validate(seed).model_dump(mode="json", exclude={"frozen_hash"})
    question = {
        "question_id": question_id,
        "question_text": question_text,
        "source_hash": source_hash,
        "registry_version": SCHEMA_VERSION,
    }
    return Registry.model_validate({"question": question, "sentences": sentences}).model_dump(
        mode="json", exclude={"frozen_hash"}
    )


def synthetic_forms(case, phase):
    qid = case["vignette_id"]
    facts = case["teaching_reference"]["facts"]
    workers = list(case["actual_worker_input_sentence_ids"])
    rows = []
    for stage in STAGE_FORMS[phase]:
        if stage == "S5b":
            units = [(None, path["path_id"], None) for path in case["teaching_reference"]["paths"]]
        else:
            unit_workers = workers if stage in {"S1", "S2", "S3", "S4"} else [None]
            units = [(fact["fact_id"], None, worker) for fact in facts for worker in unit_workers]
        for fact_id, path_id, worker_id in units:
            values = {
                "question_id": qid,
                "fact_id": fact_id,
                "path_id": path_id,
                "worker_id": worker_id,
            }
            if stage == "S1" and worker_id:
                values["actual_sentence_ids"] = case["actual_worker_input_sentence_ids"].get(
                    worker_id, []
                )
            if stage in {"S4", "S5a", "S5b"}:
                values["arm"] = "tutorial"
            if stage == "S3":
                values["publication_transition_type"] = case.get(
                    "publication_transition_type", "unknown"
                )
            model = STAGE_MODELS[stage].model_validate(values)
            rows.append({"stage": stage, "annotation": model.model_dump(mode="json")})
    return rows


def normalize_a(source, phase, asset, source_sha):
    v1.validate_a(source, phase)
    asset = TranslationAsset.model_validate(asset)
    if asset.review_mode != "pilot":
        raise ValueError("Pilot materials require a pilot TranslationAsset")
    tm = {
        pointer: pair.model_dump(mode="json")
        for pair in asset.pairs
        for pointer in pair.display_pointers
    }
    q = pair_for("/question", source["question"], tm)
    refs = []
    sentences = []
    for i, sentence in enumerate(source["reference_sentences"]):
        p = f"/reference_sentences/{i}"
        title = pair_for(p + "/title", sentence["title"], tm)
        text = pair_for(p + "/sentence_text", sentence["sentence_text"], tm)
        refs.append({"id": sentence["sentence_id"], "title": title, "text": text})
        sentences.append(
            {
                "sentence_id": sentence["sentence_id"],
                "title": sentence["title"],
                "sentence_index": sentence["sentence_index"],
                "text": sentence["sentence_text"],
                "text_hash": text_hash(sentence["sentence_text"]),
            }
        )
    registry = make_registry_form(source["case_alias"], source["question"], source_sha, sentences)
    gold = None
    if phase == "R2":
        alignment = source["benchmark_alignment"]
        gold = {
            "answer": pair_for("/benchmark_alignment/gold_answer", alignment["gold_answer"], tm),
            "supports": [
                pair_for(f"/benchmark_alignment/gold_supporting_facts/{i}/0", row[0], tm)
                for i, row in enumerate(alignment["gold_supporting_facts"])
            ],
        }
    synthetic = source["case_alias"].startswith("SYNTHETIC-")
    return {
        "case_id": source["case_alias"],
        "question": q,
        "reference": refs,
        "phase": phase,
        "synthetic": synthetic,
        "marker": MARKER if synthetic else None,
        "gold": gold,
        "facts": [],
        "paths": [],
        "observed": [],
        "exercise": GUIDE[phase]["action"],
        "registry": registry,
        "provenance": {
            "reviewer_id": None,
            "rationale": "",
            "timestamp": None,
            "registry_phase": phase,
            "judgment_status": "independent",
            "source_hashes": {"prepared_source": source_sha},
        },
        "form_kind": "registry",
        "translation_version": asset.version,
        "translation_hash": asset.frozen_hash,
        "translation_map_hash": digest(
            {k: {"en": v["english_sha256"], "ja": v["japanese_sha256"]} for k, v in tm.items()}
        ),
    }


def normalize_b(case, phase):
    v1.validate_b(case, phase)
    refs = [
        {
            "id": row["sentence_id"],
            "title": None,
            "text": synthetic_pair(row["text"], f"/reference/{i}/text"),
        }
        for i, row in enumerate(case["reference"])
    ]
    facts = [
        {
            "id": fact["fact_id"],
            "text": synthetic_pair(fact["text"], f"/teaching_reference/facts/{i}/text"),
        }
        for i, fact in enumerate(case["teaching_reference"]["facts"])
    ]
    paths = [
        {
            "id": p["path_id"],
            "facts": p["required_fact_ids"],
            "support_sets": p.get("support_set_ids", []),
            "external": synthetic_pair(
                p["proposed_external_premise"],
                f"/teaching_reference/paths/{i}/proposed_external_premise",
            )
            if "proposed_external_premise" in p
            else None,
        }
        for i, p in enumerate(case["teaching_reference"]["paths"])
    ]
    observed = []
    for worker, ids in case["actual_worker_input_sentence_ids"].items():
        observed.append(
            {
                "heading": f"Worker {worker}に実際に届いた証拠文",
                "kind": "input",
                "worker": worker,
                "items": [
                    {
                        "id": sid,
                        "text": refs[next(i for i, row in enumerate(refs) if row["id"] == sid)][
                            "text"
                        ],
                    }
                    for sid in ids
                ],
            }
        )
    if "worker_public_expression" in case:
        observed.append(
            {
                "heading": "Workerが他のAgentに公開した文章（Worker Public Expression）",
                "kind": "public",
                "items": [
                    {
                        "id": worker,
                        "text": synthetic_pair(pair, f"/worker_public_expression/{worker}"),
                    }
                    for worker, pair in case["worker_public_expression"].items()
                ],
            }
        )
    if "published_artifact" in case:
        observed.append(
            {
                "heading": "後段へ共有されたArtifact",
                "kind": "shared",
                "items": [
                    {"id": worker, "text": synthetic_pair(pair, f"/published_artifact/{worker}")}
                    for worker, pair in case["published_artifact"].items()
                ],
                "transition": case.get("publication_transition_type"),
            }
        )
    if "actual_synthesizer_input" in case:
        observed.append(
            {
                "heading": "最終回答を作るAgentに実際に届いた情報（Actual Synthesizer Input）",
                "kind": "received",
                "items": [
                    {
                        "id": worker,
                        "route": "Artifact",
                        "text": synthetic_pair(
                            pair, f"/actual_synthesizer_input/artifacts/{worker}"
                        ),
                    }
                    for worker, pair in case["actual_synthesizer_input"]["artifacts"].items()
                ]
                + [
                    {
                        "id": f"追加資料 {i + 1}",
                        "route": "Supplementary evidence",
                        "text": synthetic_pair(
                            pair, f"/actual_synthesizer_input/supplementary_evidence/{i}"
                        ),
                    }
                    for i, pair in enumerate(
                        case["actual_synthesizer_input"]["supplementary_evidence"]
                    )
                ],
            }
        )
    if "final_output" in case:
        observed.append(
            {
                "heading": "Synthesizerの最終出力",
                "kind": "final",
                "items": [
                    {
                        "id": "Final output",
                        "text": synthetic_pair(case["final_output"], "/final_output"),
                    }
                ],
            }
        )
    return {
        "case_id": case["vignette_id"],
        "question": synthetic_pair(case["question"], "/question"),
        "reference": refs,
        "phase": phase,
        "synthetic": True,
        "marker": MARKER,
        "facts": facts,
        "paths": paths,
        "support_sets": case["teaching_reference"]["support_sets"],
        "observed": observed,
        "exercise": case["exercise_prompt_ja"],
        "registry": None,
        "form_kind": "stage",
        "form": synthetic_forms(case, phase),
        "translation_version": "pilot-materials-v1.0.0",
        "translation_hash": digest(
            [
                {"en": f["text"]["en_hash"], "ja": f["text"]["ja_hash"]}
                for f in facts
                + [
                    {"text": {"en_hash": r["text"]["en_hash"], "ja_hash": r["text"]["ja_hash"]}}
                    for r in refs
                ]
            ]
        ),
    }


def normalize_packet(packet, phase, asset):
    v1.validate_packet(packet, phase)
    asset_model = TranslationAsset.model_validate(asset)
    if packet["bilingual_display"] != bilingual_projection(packet["materials"], asset_model):
        raise ValueError("Packet bilingual display differs from its frozen translation asset")
    materials = packet["materials"]
    tm = {row["material_pointer"]: row for row in packet["bilingual_display"]["pairs"]}

    def pref(pointer):
        return "/materials" + pointer

    def loc(value, pointer):
        return pair_for(pref(pointer), value, tm)

    q = loc(materials["question_text"], "/question_text")
    refs = []
    for i, sentence in enumerate(materials["reference_sentences"]):
        refs.append(
            {
                "id": sentence["sentence_id"],
                "title": loc(sentence["title"], f"/reference_sentences/{i}/title"),
                "text": loc(sentence["text"], f"/reference_sentences/{i}/text"),
            }
        )
    facts = [
        {
            "id": f["fact_id"],
            "text": loc(f["fact_text"], f"/registry_projection/facts/{i}/fact_text"),
        }
        for i, f in enumerate(materials.get("registry_projection", {}).get("facts", []))
    ]
    observed = []
    for i, worker in enumerate(materials.get("workers", [])):
        if phase == "S1":
            items = []
            for j, sentence in enumerate(worker["actual_input_sentences"]):
                items.append(
                    {
                        "id": sentence["sentence_id"],
                        "title": sentence["title"],
                        "text": loc(
                            sentence["text"], f"/workers/{i}/actual_input_sentences/{j}/text"
                        ),
                    }
                )
            observed.append(
                {
                    "heading": f"Worker {worker['worker']}に実際に届いた証拠文",
                    "kind": "input",
                    "worker": worker["worker"],
                    "items": items,
                    "available": worker["actual_input_available"],
                }
            )
        elif "public_output" in worker:
            observed.append(
                {
                    "heading": "Workerが他のAgentに公開した文章（Worker Public Expression）"
                    if phase == "S2"
                    else "Worker公開文章",
                    "kind": "public",
                    "items": [
                        {
                            "id": worker["worker"],
                            "text": localize_tree(
                                worker["public_output"], pref(f"/workers/{i}/public_output"), tm
                            ),
                        }
                    ],
                }
            )
        if "public_artifact" in worker and phase in {"S3", "S4", "S5"}:
            observed.append(
                {
                    "heading": "後段へ共有されたArtifact",
                    "kind": "shared",
                    "items": [
                        {
                            "id": worker["worker"],
                            "text": localize_tree(
                                worker["public_artifact"], pref(f"/workers/{i}/public_artifact"), tm
                            ),
                        }
                    ],
                    "transition": worker["publication_transition_type"],
                }
            )
    if phase in {"S4", "S5"}:
        ctx = materials["actual_synthesizer_input"]
        items = []
        for i, row in enumerate(ctx["artifacts"]):
            payload = row["payload"]
            items.append(
                {
                    "id": row["producer"],
                    "route": "Artifact",
                    "text": localize_tree(
                        payload, pref(f"/actual_synthesizer_input/artifacts/{i}/payload"), tm
                    ),
                }
            )
        supp = ctx["supplementary_material"]
        if supp:
            items.append(
                {
                    "id": "追加資料",
                    "route": "Supplementary evidence",
                    "text": loc(supp, "/actual_synthesizer_input/supplementary_material"),
                }
            )
        observed.append(
            {
                "heading": "最終回答を作るAgentに実際に届いた情報（Actual Synthesizer Input）",
                "kind": "received",
                "items": items,
            }
        )
    if phase == "S5":
        out = materials["final_output"]
        observed.append(
            {
                "heading": "Synthesizerの最終出力",
                "kind": "final",
                "items": [
                    {"id": "Final output", "text": localize_tree(out, pref("/final_output"), tm)}
                ],
            }
        )
    registry = deepcopy(packet["form"]["registry"]) if phase in {"R1", "R2"} else None
    provenance = deepcopy(packet["form"]["provenance"]) if phase in {"R1", "R2"} else None
    if registry and phase == "R2" and materials.get("own_locked_R1_registry"):
        registry = deepcopy(materials["own_locked_R1_registry"])
    return {
        "case_id": packet["case_code"],
        "question": q,
        "reference": refs,
        "phase": phase,
        "synthetic": False,
        "gold": (
            {
                "answer": loc(
                    materials["benchmark_alignment"]["gold_answer"],
                    "/benchmark_alignment/gold_answer",
                ),
                "supports": [
                    loc(row[0], f"/benchmark_alignment/gold_supporting_facts/{i}/0")
                    for i, row in enumerate(
                        materials["benchmark_alignment"]["gold_supporting_facts"]
                    )
                ],
            }
            if phase == "R2"
            else None
        ),
        "facts": facts,
        "paths": [
            {
                "id": p["path_id"],
                "facts": [
                    m["fact_id"]
                    for m in materials.get("registry_projection", {}).get("memberships", [])
                    if m["path_id"] == p["path_id"] and m["required_within_path"] == "yes"
                ],
            }
            for p in materials.get("registry_projection", {}).get("paths", [])
        ],
        "observed": observed,
        "exercise": GUIDE[phase]["action"],
        "registry": registry,
        "provenance": provenance,
        "form": deepcopy(packet["form"]) if phase not in {"R1", "R2"} else None,
        "form_kind": "registry" if phase in {"R1", "R2"} else "stage",
        "translation_version": asset_model.version,
        "translation_hash": asset_model.frozen_hash,
    }


def stage_rows(case, phase):
    if case["form_kind"] == "registry":
        return []
    return case["form"]


def prepare_cases(value, phase, asset, source_sha):
    units = value if isinstance(value, list) else [value]
    if not units:
        raise ValueError("At least one case is required")
    cases = []
    for unit in units:
        if "vignette_id" in unit:
            case = normalize_b(unit, phase)
        elif "case_alias" in unit:
            case = normalize_a(unit, phase, asset, source_sha)
        else:
            if asset is None:
                raise ValueError("Fixed translation asset required for canonical packet")
            case = normalize_packet(unit, phase, asset)
        if "registry" not in case:
            case["registry"] = None
        if phase in {"S1", "S2", "S3", "S4", "S5"} and case["form_kind"] == "stage":
            case["form"] = stage_rows(case, phase)
        cases.append(case)
    if len({c["case_id"] for c in cases}) != len(cases):
        raise ValueError("Duplicate case aliases")
    return cases


def paragraph(pair, title=None):
    ja = esc(pair.get("ja", ""))
    en = esc(pair.get("en", ""))
    details = (
        f'<details><summary>英語原文を確認</summary><p class="en">{en}</p></details>' if en else ""
    )
    return f'<div class="ja">{ja}</div>{details}'


def editor_html(case, index, count, source_hash):
    return ""  # The phase controller creates the accessible form from phase-only JSON.


def overview_html():
    steps = [
        ("R1", "元の資料だけを見て、答えの根拠となる事実と文章を整理する。"),
        ("R2", "正解とその根拠となる文章を追加して、自分の候補を確認・調整する。"),
        (
            "確認する事実を固定",
            "この後モデル出力を見ても、必要な事実の定義を都合よく変更しないよう固定する。",
        ),
        *[(s, GUIDE[s]["title"]) for s in STAGE_FORMS],
    ]
    cards = "".join(
        f'<article class="card"><span class="badge">{esc(name)}</span><p>{esc(desc)}</p></article>'
        for name, desc in steps
    )
    flow = "相談せず個別に判定　→　不一致を確認　→　理由を残して話し合い　→　判定基準を修正　→　必要なら練習をやり直す　→　人間が基準の固定を承認　→　本判定"
    return page_shell(
        "全体ガイド",
        '<header><h1>最初の5分：何を確認するの？</h1><p>質問 → AI①が資料を読む → AI①が内容を伝える → 共有された情報 → AI②が最終回答を作る → 最終回答</p><p>このレビューでは、事実がこの流れの途中で消えたり変わったりしていないかを確認します。AIの内部思考は推測しません。</p><p>事実を整理する準備と、固定した事実を文章と比較する判定は別の作業です。S1以降では、画面に示された事実だけを比較します。</p><p>日本語を主に読んで構いません。意味の基準は英語原文です。迷ったら原文を確認し、それでも決められなければ「判断できない」を選んでください。</p></header><section class="card"><h2>確認する順番</h2><div class="columns">'
        + cards
        + '</div></section><section class="card"><h2>判定とMain Reviewまでの流れ</h2><p>'
        + esc(flow)
        + "</p><p>2名は相手に相談せず個別に記録します。最初の票を保存した後に不一致を確認し、必要なら基準を修正して練習をやり直します。人間の承認前に本判定は始まりません。</p></section>"
        + '<section class="card"><h2>練習前の簡単な例</h2><p class="mark">TUTORIAL EXAMPLE / NOT REVIEW DATA</p><p>以下は人工の説明例です。判定票には保存しません。</p><p><b>今回確認する事実：</b>青葉研究所は2012年に開設された。</p><p><b>最初のAIが読んだ文章：</b>青葉研究所は2012年に開設された。</p><p>この場合は「ある：この事実を判断できる内容が書かれている」です。</p><p>次に、他のAIへ伝えた文章を比べる場面を考えます。</p><ul><li>「青葉研究所は2012年に開設された。」なら、事実が正しく残っています。</li><li>「青葉研究所は開設された。」なら、年が欠けているため一部だけです。</li><li>「青葉研究所は2013年に開設された。」なら、年が矛盾して変わっています。</li><li>「天気は晴れです。」だけなら、この事実は書かれていません。</li><li>「その年に開設された。」だけで「その年」が何年か決められないなら、判断できない場合があります。</li></ul><p>最初の判定はAIが読んだ文章を、次の判定はAIが他へ伝えた文章を比べます。AIの頭の中を想像する必要はありません。段階ごとの選択肢が異なるため、その画面の説明を使ってください。</p></section><p class="privacy">このガイドは説明用です。実際の資料と回答入力は段階ごとのHTMLにあります。</p>',
    )


def page_shell(title, body, scripts="", inline_data=None):
    css = (HERE / "style.css").read_text(encoding="utf-8")
    data_tag = (
        ""
        if inline_data is None
        else '<script id="review-data" type="application/json">'
        + js_json(inline_data)
        + "</script>"
    )
    return (
        '<!doctype html>\n<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
        "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'\">"
        f"<title>{esc(title)}</title><style>{css}</style></head><body><main>{body}{data_tag}{scripts}</main></body></html>\n"
    ).encode()


def ui_script(storage_key, phase):
    all_options = {
        "S1": ["complete", "partial", "none", "unclear"],
        "S2": ["correct", "partial", "distorted", "absent", "unclear"],
        "S3": ["retained", "partial_loss", "distorted", "lost", "unclear", "NA"],
        "S4": ["correct", "partial", "distorted", "absent", "unclear"],
        "S5a": ["reflected", "contradicted", "not_asserted", "unclear", "NA"],
        "S5b": ["fully_supported", "partially_supported", "unsupported", "unclear", "NA"],
    }
    phases = STAGE_FORMS.get(phase, ())
    options = {stage: all_options[stage] for stage in phases}
    label_subset = {
        value: LABELS[value] for value in {v for values in options.values() for v in values}
    }
    route_labels = {
        "artifact": "共有Artifactを通じて",
        "supplementary_evidence": "追加資料として",
        "both": "両方の経路",
        "neither": "どちらにも含まれない",
        "unclear": "記録から判断できない",
    }
    script = (
        "<script>\n"
        + r"""(()=>{
"use strict";
const cases=JSON.parse(document.getElementById("review-data").textContent), keyBase="review-v2:"+"""
        + js_json(storage_key)
        + r''';
const guide=cases.guide, rows=cases.cases, stage=cases.phase;
const reviewerId=new URLSearchParams(location.search).get("reviewer")||"";
const root=document.getElementById("case-screen"),status=document.getElementById("save-status");
if(!/^[A-Za-z0-9_-]{1,64}$/.test(reviewerId)){root.innerHTML='<section class="card"><h1>Reviewer IDが必要です</h1><p>index.htmlへ戻り、担当者から指定された仮名IDを入力してください。</p><a href="index.html">case一覧へ戻る</a></section>';return}
const key=keyBase+":"+reviewerId;
let index=Number(new URLSearchParams(location.search).get("case")||0), memory={};
if(!Number.isInteger(index)||index<0||index>=rows.length)index=0;
try{memory=JSON.parse(localStorage.getItem(key)||"{}")}catch(_e){memory={}}
let persistent=true;
try{localStorage.setItem(key,JSON.stringify(memory))}catch(_e){persistent=false}
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const clone=x=>JSON.parse(JSON.stringify(x));
const stateFor=()=>memory[rows[index].case_id]||(memory[rows[index].case_id]={labels:{},notes:{},reviewer:reviewerId,evidence:{},naReasons:{},routes:{}});
const save=()=>{try{localStorage.setItem(key,JSON.stringify(memory));status.textContent=persistent?"このブラウザに下書きを保存しました。":"このタブ内に一時保存中です。JSONをダウンロードしてください。"}catch(_e){persistent=false;status.textContent="ブラウザが保存を許可しません。JSONをダウンロードしてください。"}};
function pair(p){if(p===null||p===undefined)return "";if(Array.isArray(p))return p.map(pair).join("");if(typeof p!=="object")return '<div class="ja">'+esc(p)+'</div>';if(Object.hasOwn(p,"ja")){return '<div class="ja">'+esc(p.ja)+'</div>'+(p.en?'<details><summary>英語原文を確認</summary><div class="en">'+esc(p.en)+'</div></details>':"")}return Object.entries(p).map(([k,v])=>'<div class="sentence"><b>'+esc(k)+'</b>'+pair(v)+'</div>').join("")}
function compare(){const c=rows[index];let base='<section class="card question"><h2>質問</h2>'+pair(c.question)+'</section><section class="card"><h2>基準となる情報</h2>';
for(const f of c.facts||[])base+='<div class="fact"><span class="id">'+esc(f.id)+'</span>'+pair(f.text)+'</div>';
for(const s of c.reference||[])base+='<div class="sentence"><span class="id">'+esc(s.id)+'</span>'+(s.title?'<p>'+pair(s.title)+'</p>':"")+pair(s.text)+'</div>';
if(c.paths?.length)base+='<details><summary>証拠の組・path IDなどの詳細</summary><pre>'+esc(JSON.stringify({paths:c.paths,support_sets:c.support_sets},null,2))+'</pre></details>';
if(c.gold)base+='<div class="fact"><b>Gold Answer</b>'+pair(c.gold.answer)+'</div>'+c.gold.supports.map(x=>'<div class="fact"><b>Gold Supporting Fact</b>'+pair(x)+'</div>').join("");
base+='</section>';let obs='<section class="card observed"><h2>この段階で実際に観測された情報</h2>';
for(const group of c.observed||[]){obs+='<div class="entry"><h3>'+esc(group.heading)+'</h3>'+(group.available===false?'<p>実際の入力記録がありません。</p>':"")+(group.transition?'<p>公開の仕組み：'+esc(group.transition)+'</p>':"");for(const item of group.items||[]){const route=routeLabels[item.route]||item.route;obs+='<div class="sentence">'+(item.id?'<span class="id">'+esc(item.id)+'</span>':"")+(item.route?'<span class="badge">'+esc(route)+'</span>':"")+(item.title?'<p>'+pair(item.title)+'</p>':"")+pair(item.text)+'</div>'}obs+='</div>'}obs+='</section>';return '<div class="columns">'+base+obs+'</div>'}
const labelText=__LABEL_TEXT__;
const stateOptions=__STATE_OPTIONS__;
const routeLabels=__ROUTE_LABELS__;
const transitionLabels={"separate_records":"Workerの公開文章とは別のArtifact記録があります","identity_alias":"ArtifactはWorker公開文章と同じ記録を指し、独立した移行段階はありません","unknown":"記録から移行の有無を特定できません"};
function renderLabels(){let c=rows[index],s=stateFor();if(c.form_kind==="registry")return '<div class="registry-editor">'+registryEditor(c,s)+'</div>';let out='<section class="card"><h2>あなたの判定</h2><p>Reviewer ID：'+esc(reviewerId)+'</p><p class="subtle">partialは必要な要素が足りない状態、distortedは重要な内容が矛盾して変わった状態です。absentは該当内容が見当たらない状態、unclearは資料を読んでも区別できない状態です。記録自体がない場合はunclearにせず、担当者へ報告してください。</p>';
for(let i=0;i<c.form.length;i++){let row=c.form[i],ann=row.annotation,field="state",opts=stateOptions[row.stage]||[];if(ann.publication_transition_type==="identity_alias")opts=["NA"];if(ann.applicability==="not_applicable")opts=["NA"];let target=ann.fact_id?c.facts.find(f=>f.id===ann.fact_id):null;let path=ann.path_id?c.paths.find(p=>p.id===ann.path_id):null;let targetHtml=target?pair(target.text):path?'<p>この道筋に登録された必要事実：'+esc((path.facts||[]).join("、"))+'</p>':"";out+='<fieldset class="entry"><legend>'+esc(row.stage)+': '+esc(ann.fact_id||ann.path_id||"判定")+(ann.worker_id?' · '+esc(ann.worker_id):"")+'</legend>'+targetHtml+'<p>下の説明で判断し、意味の基準は英語原文です。</p>';
for(const value of opts){let checked=s.labels[i]===value;out+='<label class="choice"><input type="radio" name="label-'+i+'" value="'+esc(value)+'" '+(checked?"checked":"")+'>'+esc(labelText[value]||value)+'<span class="canonical">Code: '+esc(value)+'</span></label>'}
if(row.stage==="S4")out+='<label>実際に届いた経路<select data-route="'+i+'"><option value="">選択してください</option>'+["artifact","supplementary_evidence","both","neither","unclear"].map(x=>'<option value="'+x+'" '+(s.routes?.[i]===x?"selected":"")+'>'+esc(routeLabels[x])+'</option>').join("")+'</select></label>';
if(s.labels[i]==="NA"&&ann.publication_transition_type!=="identity_alias")out+='<label>この段階が該当しない理由（必須）<textarea class="note" data-na-reason="'+i+'">'+esc(s.naReasons?.[i]||"")+'</textarea></label>';
out+='<label>判断理由・unclearの場合の迷った点<textarea class="note" data-note="'+i+'">'+esc(s.notes[i]||"")+'</textarea></label><label>根拠sentence ID（任意・カンマ区切り）<input type="text" data-evidence="'+i+'" value="'+esc((s.evidence?.[i]||[]).join(", "))+'"></label></fieldset>'}
out+='<button class="primary" id="export">回答をJSONとして保存</button> <button id="clear-case">このcaseの下書きを消す</button></section>';return out}
function registryEditor(c,s){let r=s.registry||clone(c.registry);s.registry=r;let out='<section class="card"><h2>回答に必要な事実と道筋を記録</h2><p>Factは「回答に必要な事実」、Support Setは「その事実を支える証拠文の組（代替候補はどれか1組でよい）」、Pathは「回答へ至る道筋」です。道筋に必要な複数の事実はすべてそろう必要があります。</p><p>画面の入力は既存Registry schemaに保存します。英語原文が意味の基準です。事実は日本語で記録できます。</p><p>Reviewer ID：'+esc(reviewerId)+'</p><h3>回答に必要な事実（Fact）</h3><div id="facts">';
for(let i=0;i<r.facts.length;i++)out+=factRow(r.facts[i],i);out+='</div><button type="button" id="add-fact">事実を追加</button><h3>証拠の組</h3><div id="sets">';for(let i=0;i<r.support_sets.length;i++)out+=setRow(r.support_sets[i],i,c.reference);out+='</div><button type="button" id="add-set">証拠の組を追加</button><h3>回答までの道筋</h3><div id="paths">';for(let i=0;i<r.paths.length;i++)out+=pathRow(r.paths[i],i);out+='</div><button type="button" id="add-path">道筋を追加</button><h3>道筋に必要な事実</h3><div id="members">';for(let i=0;i<r.memberships.length;i++)out+=memberRow(r.memberships[i],i,r);out+='</div><button type="button" id="add-member">事実を道筋へ追加</button><p><button class="primary" id="export">Registry ballot JSONを保存</button> <button id="clear-case">このcaseの下書きを消す</button></p></section>';return out}
function select(name,values,chosen,labels={}){return '<select name="'+name+'">'+values.map(v=>'<option value="'+esc(v)+'" '+(v===chosen?'selected':'')+'>'+esc(labels[v]||v)+'</option>').join("")+'</select>'}
function factRow(x,i){const basis=stage==="R1"?["raw_discovery"]:["raw_discovery","gold_anchor","both"];return '<div class="entry fact-row"><label>Fact ID（事実番号）<input name="fact_id" value="'+esc(x.fact_id)+'"></label><label>必要な事実<textarea name="fact_text">'+esc(x.fact_text)+'</textarea></label><label>事実の種類'+select("fact_type",["atomic_fact","relation_step","answer_claim"],x.fact_type,{atomic_fact:"個別の事実",relation_step:"事実どうしの関係",answer_claim:"質問への回答内容"})+'</label><label>この事実と基準情報の関係'+select("reference_basis",basis,x.reference_basis,{raw_discovery:"参考文書から発見",gold_anchor:"Gold情報と対応",both:"両方に対応"})+'</label></div>'}
function setRow(x,i,refs){return '<div class="entry set-row"><label>Support Set ID（証拠の組番号）<input name="support_set_id" value="'+esc(x.support_set_id)+'"></label><label>対象Fact ID（対象となる事実番号）<input name="fact_id" value="'+esc(x.fact_id)+'"></label><div>この事実を支える証拠文を選択<div class="checklist">'+refs.map(a=>'<label><input type="checkbox" name="sentence" value="'+esc(a.id)+'" '+(x.evidence_sentence_ids.includes(a.id)?'checked':'')+'>'+esc(a.id)+'</label>').join("")+'</div></div><label>この証拠文の組だけで事実を十分に支えますか'+select("support_set_sufficient",["yes","no","unclear"],x.support_set_sufficient||"unclear",{yes:"はい",no:"いいえ",unclear:"判断できない"})+'</label></div>'}
function pathRow(x,i){const basis=stage==="R1"?["raw_discovered_alternative"]:["gold_anchored","raw_discovered_alternative"];return '<div class="entry path-row"><label>Path ID（回答までの道筋番号）<input name="path_id" value="'+esc(x.path_id)+'"></label><label>道筋の種類'+select("path_basis",basis,x.path_basis,{gold_anchored:"Gold情報に基づく道筋",raw_discovered_alternative:"参考文書から見つけた別の道筋"})+'</label><label>この道筋が答える内容<textarea name="target_answer">'+esc(x.target_answer)+'</textarea></label><label>この道筋は質問に答える根拠として妥当ですか'+select("validity",["yes","no","unclear"],x.validity||"unclear",{yes:"妥当",no:"妥当ではない",unclear:"判断できない"})+'</label></div>'}
function memberRow(x,i,r){let fopts=r.facts.map(f=>f.fact_id),popts=r.paths.map(p=>p.path_id);return '<div class="entry member-row"><label>回答までの道筋'+select("path_id",popts,x.path_id)+'</label><label>その道筋に含める事実'+select("fact_id",fopts,x.fact_id)+'</label><label>この道筋を成立させるために必要か'+select("required_within_path",["yes","no","unclear"],x.required_within_path||"unclear",{yes:"必要",no:"なくてもこの道筋は成り立つ",unclear:"判断できない"})+'</label><label>該当する証拠の組番号（複数可）<input name="support_set_ids" value="'+esc((x.support_set_ids||[]).join(", "))+'"></label></div>'}
function collectRegistry(){const c=rows[index];let base=clone(stateFor().registry||c.registry);const all=(selector,fn)=>[...root.querySelectorAll(selector)].map(fn);base.facts=all(".fact-row",e=>({fact_id:e.querySelector('[name="fact_id"]').value.trim(),fact_text:e.querySelector('[name="fact_text"]').value.trim(),fact_type:e.querySelector('[name="fact_type"]').value,reference_basis:e.querySelector('[name="reference_basis"]').value})).filter(x=>x.fact_id&&x.fact_text);base.support_sets=all(".set-row",e=>({support_set_id:e.querySelector('[name="support_set_id"]').value.trim(),fact_id:e.querySelector('[name="fact_id"]').value.trim(),evidence_sentence_ids:[...e.querySelectorAll('[name="sentence"]:checked')].map(a=>a.value),support_set_sufficient:e.querySelector('[name="support_set_sufficient"]').value})).filter(x=>x.support_set_id&&x.fact_id&&x.evidence_sentence_ids.length);base.paths=all(".path-row",e=>({path_id:e.querySelector('[name="path_id"]').value.trim(),path_basis:e.querySelector('[name="path_basis"]').value,target_answer:e.querySelector('[name="target_answer"]').value.trim(),validity:e.querySelector('[name="validity"]').value})).filter(x=>x.path_id&&x.target_answer);base.memberships=all(".member-row",e=>({question_id:base.question.question_id,path_id:e.querySelector('[name="path_id"]').value,fact_id:e.querySelector('[name="fact_id"]').value,required_within_path:e.querySelector('[name="required_within_path"]').value,support_set_ids:e.querySelector('[name="support_set_ids"]').value.split(",").map(x=>x.trim()).filter(Boolean)})).filter(x=>x.path_id&&x.fact_id&&x.support_set_ids.length);return base}
function draw(){const c=rows[index],s=stateFor();let marker=c.synthetic?'<p class="mark">SYNTHETIC CALIBRATION MATERIAL · NOT STUDY DATA · NOT MODEL OUTPUT</p>':"";let gold=c.gold?'<section class="card"><h2>Gold情報（R2）</h2>'+pair(c.gold.answer)+c.gold.supports.map(pair).join("")+'</section>':"";root.innerHTML=marker+'<div class="topbar"><span class="badge">'+esc(stage)+': '+esc(guide.title)+'</span><span>Case '+(index+1)+' / '+rows.length+' · '+esc(c.case_id)+'</span></div><h1>このcaseを確認します</h1><div class="taskbox"><h2>今回やること</h2><div class="taskgrid"><p><b>目的</b><br>'+esc(guide.purpose)+'</p><p><b>今回見るもの</b><br>'+esc(guide.see)+'</p><p><b>比較するもの</b><br>'+esc(guide.compare)+'</p><p><b>あなたへの質問</b><br>'+esc(guide.answer)+'</p><p><b>この段階では見ないもの</b><br>'+esc(guide.avoid)+'</p><p><b>意味の基準</b><br>日本語訳を先に読み、迷ったら英語原文を確認してください。</p></div></div>'+compare()+gold+'<section class="card"><h2>練習の案内</h2><p>'+esc(c.exercise)+'</p></section>'+renderLabels()+'<div class="navrow"><button id="previous" '+(index===0?'disabled':'')+'>前のcase</button><span>'+esc(c.case_id)+'　'+(index+1)+' / '+rows.length+'</span><button id="next" '+(index===rows.length-1?'disabled':'')+'>次のcase</button></div><p class="status" id="save-status">'+(persistent?'このブラウザに保存できます。':'このブラウザではlocalStorageが使えません。回答JSONを保存してください。')+'</p>';
root.querySelector("#previous")?.addEventListener("click",()=>navigate(-1));root.querySelector("#next")?.addEventListener("click",()=>navigate(1));const reviewer=root.querySelector("#reviewer");reviewer?.addEventListener("input",()=>{stateFor().reviewer=reviewer.value;save()});
root.querySelectorAll('input[type="radio"]').forEach(el=>el.addEventListener("change",()=>{stateFor().labels[el.name.split("-")[1]]=el.value;save();draw()}));root.querySelectorAll("select[data-route]").forEach(el=>el.addEventListener("change",()=>{stateFor().routes[el.dataset.route]=el.value;save()}));root.querySelectorAll("textarea[data-note]").forEach(el=>el.addEventListener("input",()=>{stateFor().notes[el.dataset.note]=el.value;save()}));root.querySelectorAll("textarea[data-na-reason]").forEach(el=>el.addEventListener("input",()=>{stateFor().naReasons[el.dataset.naReason]=el.value;save()}));root.querySelectorAll("input[data-evidence]").forEach(el=>el.addEventListener("input",()=>{stateFor().evidence=stateFor().evidence||{};stateFor().evidence[el.dataset.evidence]=el.value.split(",").map(x=>x.trim()).filter(Boolean);save()}));
root.querySelector("#export")?.addEventListener("click",exportBallot);root.querySelector("#clear-case")?.addEventListener("click",()=>{delete memory[c.case_id];save();draw()});document.getElementById("clear-all")?.addEventListener("click",()=>{try{localStorage.removeItem(key)}catch(_e){};for(const id of Object.keys(memory))delete memory[id];draw()});
for(const [button,collection,prefix,make] of [["#add-fact","facts","F",x=>({fact_id:x,fact_text:"",fact_type:"atomic_fact",reference_basis:stage==="R1"?"raw_discovery":"both"})],["#add-set","support_sets","SS",x=>({support_set_id:x,fact_id:"",evidence_sentence_ids:[],support_set_sufficient:"unclear"})],["#add-path","paths","P",x=>({path_id:x,path_basis:stage==="R1"?"raw_discovered_alternative":"gold_anchored",target_answer:"",validity:"unclear"})]])root.querySelector(button)?.addEventListener("click",()=>{stateFor().registry=collectRegistry();let a=stateFor().registry[collection],n=a.length+1;a.push(make(prefix+String(n).padStart(3,"0")));save();draw()});
root.querySelector("#add-member")?.addEventListener("click",()=>{stateFor().registry=collectRegistry();const r=stateFor().registry;r.memberships.push({question_id:r.question.question_id,path_id:r.paths[0]?.path_id||"",fact_id:r.facts[0]?.fact_id||"",required_within_path:"yes",support_set_ids:[]});save();draw()});
root.querySelectorAll(".registry-editor select,.registry-editor input,.registry-editor textarea").forEach(el=>el.addEventListener("change",()=>{stateFor().registry=collectRegistry();save()}));
}
function navigate(delta){if(rows[index].form_kind==="registry")stateFor().registry=collectRegistry();save();index=Math.max(0,Math.min(rows.length-1,index+delta));draw()}
function exportBallot(){const c=rows[index],s=stateFor();if(!s.reviewer?.trim()){alert("Reviewer ID（仮名）を入力してください。");return}let ballot;
if(c.form_kind==="registry"){let registry=collectRegistry();try{registry=Object.assign(registry,{judgments:[],frozen_hash:null});const now=new Date().toISOString();ballot={registry:registry,provenance:{...c.provenance,reviewer_id:reviewerId,timestamp:now,registry_phase:stage,judgment_status:"independent"}};validateRegistry(ballot.registry)}catch(e){alert("Registryの参照関係を確認してください: "+e.message);return}}
else{ballot=clone(c.form);for(let i=0;i<ballot.length;i++){const row=ballot[i],a=row.annotation,selected=s.labels[i];if(!selected){alert("すべての判定を選んでください。");return}const note=s.notes[i]||"";if(selected==="unclear"&&!note.trim()){alert("unclearを選んだ場合は、判断できない理由を記録してください。");return}a.state=selected;a.rationale=note||null;a.evidence_pointer=s.evidence?.[i]||[];a.reviewer_id=reviewerId;a.codebook_version="'''
        + CODEBOOK_VERSION
        + r"""";if(row.stage==="S4"){if(!s.routes?.[i]){alert("S4では情報が届いた経路も選んでください。");return}a.received_via=s.routes[i]}if(selected==="NA"){if(a.publication_transition_type==="identity_alias"){a.applicability="not_applicable";a.applicability_reason="no_separate_transition"}else{const reason=s.naReasons?.[i]||"";if(!reason.trim()){alert("NAを選んだ場合は、該当しない理由を記録してください。");return}a.applicability="not_applicable";a.applicability_reason=reason}}}if(!validateStageForm(ballot,stage)){alert("選択内容が既存ballot schemaに合いません。");return}}
const blob=new Blob([JSON.stringify(ballot,null,2)+"\n"],{type:"application/json;charset=utf-8"}),url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download=c.case_id+"."+reviewerId+".ballot.json";a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
function validateStageForm(rows,phase){const allowed=[...new Set(cases.cases.flatMap(c=>(c.form||[]).map(x=>x.stage)))];return Array.isArray(rows)&&rows.every(x=>allowed.includes(x.stage)&&x.annotation&&typeof x.annotation.question_id==="string"&&x.annotation.state&&Object.keys(x).sort().join(",")==="annotation,stage")}
function validateRegistry(r){if(!r.question||!Array.isArray(r.sentences)||!Array.isArray(r.facts)||!Array.isArray(r.support_sets)||!Array.isArray(r.paths)||!Array.isArray(r.memberships))throw Error("registry fields");let facts=new Set(r.facts.map(x=>x.fact_id)),sent=new Set(r.sentences.map(x=>x.sentence_id)),sets=new Map(r.support_sets.map(x=>[x.support_set_id,x]));for(const s of r.support_sets)if(!facts.has(s.fact_id)||!s.evidence_sentence_ids.length||s.evidence_sentence_ids.some(id=>!sent.has(id)))throw Error("support set");for(const m of r.memberships)if(!facts.has(m.fact_id)||!r.paths.some(p=>p.path_id===m.path_id)||!m.support_set_ids.length||m.support_set_ids.some(id=>sets.get(id)?.fact_id!==m.fact_id))throw Error("path membership")}
draw();
})();</script>"""
    )
    script = script.replace(
        "const labelText=__LABEL_TEXT__;", "const labelText=" + js_json(label_subset) + ";"
    )
    script = script.replace(
        "const stateOptions=__STATE_OPTIONS__;", "const stateOptions=" + js_json(options) + ";"
    )
    script = script.replace(
        "const routeLabels=__ROUTE_LABELS__;", "const routeLabels=" + js_json(route_labels) + ";"
    )
    script = script.replace(
        "公開の仕組み：'+esc(group.transition)",
        "共有前後の記録：'+esc(transitionLabels[group.transition]||group.transition)",
    )
    # Stage review is one fixed canonical annotation unit per screen. Registry
    # discovery remains a separate R1/R2 task; no registry editing is exposed here.
    if phase in STAGE_FORMS:
        # Do not ship unused registry editing or the old multi-fact screen in
        # stage pages. Only same-stage records and the fixed ballot are needed.
        for start, end in (
            ("function compare(){", "const labelText="),
            ("function renderLabels(){", "function exportBallot(){"),
        ):
            left, tail = script.split(start, 1)
            script = left + end + tail.split(end, 1)[1]
        script = script.replace(
            "draw();\n})();",
            (HERE / "stage_tasks.js").read_text(encoding="utf-8") + "\ndraw();\n})();",
        )
    script = script.replace(
        "status.textContent=", 'document.getElementById("save-status").textContent='
    )
    return script


def page_html(cases, phase, storage_key):
    guide = GUIDE[phase]
    body = (
        '<header><div class="topbar"><span class="badge">'
        + esc(phase)
        + '</span><a href="index.html">case一覧へ</a><a href="overview.html">全体の流れを見る</a></div><h1>'
        + esc(guide["title"])
        + '</h1><div class="progress"><span id="progressbar"></span></div><p id="counter" aria-live="polite"></p></header><section id="case-screen"></section><section class="card"><h2>保存・個人情報</h2><p>入力は仮名Reviewer IDごとに、このブラウザのlocalStorageへ保存されます。共有PCでは作業後にcase下書きを消し、下のボタンとブラウザのfile-page/site storage削除を使ってください。fileページで保存が制限される場合は、タブを閉じる前にJSONをダウンロードしてください。回答は元の資料JSONへ書き戻しません。</p><p>localStorageはこの端末の同じブラウザprofileを使う人には読めるため、Reviewerごとに分けた端末/profileを利用してください。Hashやauthor pathは画面の本文に表示しません。</p><button id="clear-all">このReviewer IDの下書きをすべて消す</button></section>'
    )
    script = ui_script(storage_key, phase)
    # Add a tiny same-phase progress/index bridge. Only aliases and current phase appear here.
    script = script.replace(
        "function draw(){const c=rows[index]",
        'function draw(){document.getElementById("counter").textContent="進捗："+(index+1)+" / "+rows.length;document.getElementById("progressbar").style.width=((index+1)/rows.length*100)+"%";const c=rows[index]',
    )
    return page_shell(
        f"{phase} Reviewer",
        body,
        script,
        {"phase": phase, "guide": guide, "cases": reviewer_projection(cases)},
    )


def index_html(cases, phase, storage_key):
    guide = GUIDE[phase]
    entries = "".join(
        f'<li><a href="#" class="case-link" data-index="{i}">Case {i + 1} / {len(cases)} · {esc(case["case_id"])}</a><span data-progress="{i}">未回答</span></li>'
        for i, case in enumerate(cases)
    )
    body = (
        '<header><a href="overview.html">全体の流れ</a><span class="badge">'
        + esc(phase)
        + "</span><h1>"
        + esc(guide["title"])
        + '</h1></header><section class="taskbox"><h2>この段階の目的</h2><p>'
        + esc(guide["purpose"])
        + "</p><p><b>今回すること：</b>"
        + esc(guide["action"])
        + "</p><p><b>比較するもの：</b>"
        + esc(guide["compare"])
        + "</p><p><b>回答する質問：</b>"
        + esc(guide["answer"])
        + "</p><p><b>この段階では見ないもの：</b>"
        + esc(guide["avoid"])
        + '</p></section><section class="card"><h2>Reviewer IDと進捗</h2>'
        '<label>担当者から指定された仮名ID<input id="reviewer-id" type="text" maxlength="64" autocomplete="off"></label>'
        "<p>実名やメールアドレスではなく、事前に指定された英数字の仮名IDを入力します。</p>"
        '<div class="progress"><span id="index-progress"></span></div><p id="index-count"></p><ul>'
        + entries
        + '</ul><button class="primary" id="start-review">Reviewを開始する</button></section>'
        '<p class="privacy">日本語訳を先に読み、判断に迷った場合は英語原文を確認してください。回答は仮名IDごとにこのブラウザへ下書き保存し、JSONとして別ファイルへ出力します。</p>'
    )
    case_ids = [case["case_id"] for case in cases]
    index_script = (
        "<script>const ids="
        + js_json(case_ids)
        + ',base="review-v2:"+'
        + js_json(storage_key)
        + r""";const input=document.getElementById("reviewer-id");function valid(){return /^[A-Za-z0-9_-]{1,64}$/.test(input.value.trim())}function refresh(){let n=0,s={};try{if(valid())s=JSON.parse(localStorage.getItem(base+":"+input.value.trim())||"{}")}catch(_e){}ids.forEach((id,i)=>{const x=s[id]||{},started=!!(Object.keys(x.labels||{}).length||x.registry?.facts?.length);if(started)n++;const e=document.querySelector('[data-progress="'+i+'"]');if(e)e.textContent=started?"入力あり":"未回答"});document.getElementById("index-count").textContent="入力を始めたcase："+n+" / "+ids.length;document.getElementById("index-progress").style.width=(n/ids.length*100)+"%"}function go(i){if(!valid()){alert("担当者から指定された仮名Reviewer IDを入力してください。");return}location.href="review.html?reviewer="+encodeURIComponent(input.value.trim())+"&case="+i}input.addEventListener("input",refresh);document.querySelectorAll(".case-link").forEach(a=>a.addEventListener("click",e=>{e.preventDefault();go(Number(a.dataset.index))}));document.getElementById("start-review").addEventListener("click",()=>go(0));refresh();</script>"""
    )
    return page_shell(f"{phase} case一覧", body, index_script)


def validate_export(ballot, phase):
    if phase in {"R1", "R2"}:
        if set(ballot) != {"registry", "provenance"}:
            raise ValueError("Registry ballot wrapper mismatch")
        Registry.model_validate(ballot["registry"])
        return True
    allowed = STAGE_FORMS[phase]
    if not isinstance(ballot, list):
        raise ValueError("Stage ballot must be the canonical form array")
    if not ballot:
        raise ValueError("Empty stage ballot")
    for row in ballot:
        if set(row) != {"stage", "annotation"} or row["stage"] not in allowed:
            raise ValueError("Unexpected ballot stage")
        STAGE_MODELS[row["stage"]].model_validate(row["annotation"])
    return True


def make_stage_ballot(form, selections, notes, reviewer_id, evidence=None, routes=None):
    """Apply UI choices to the existing v3 blank-form shape, then validate it."""
    ballot = deepcopy(form)
    evidence = evidence or {}
    routes = routes or {}
    if not reviewer_id.strip() or len(selections) != len(ballot):
        raise ValueError("Reviewer and every label are required")
    for i, row in enumerate(ballot):
        annotation = row["annotation"]
        state = selections[i]
        note = notes.get(str(i), "")
        if state == "unclear" and not note.strip():
            raise ValueError("unclear requires an ambiguity note")
        annotation["state"] = state
        annotation["rationale"] = note or None
        annotation["evidence_pointer"] = evidence.get(str(i), [])
        annotation["reviewer_id"] = reviewer_id.strip()
        annotation["codebook_version"] = CODEBOOK_VERSION
        if row["stage"] == "S4":
            route = routes.get(str(i))
            if route not in {"artifact", "supplementary_evidence", "both", "neither", "unclear"}:
                raise ValueError("S4 requires an existing received_via route label")
            annotation["received_via"] = route
        if annotation.get("publication_transition_type") == "identity_alias" and state == "NA":
            annotation["applicability"] = "not_applicable"
            annotation["applicability_reason"] = "no_separate_transition"
    validate_export(
        ballot, "S5" if {x["stage"] for x in ballot} <= {"S5a", "S5b"} else ballot[0]["stage"]
    )
    return ballot


def build(source_path, phase, destination, translation_path=None):
    source_path, destination = Path(source_path), Path(destination)
    source = read(source_path)
    asset = read(translation_path) if translation_path else None
    source_sha = file_hash(source_path)
    cases = prepare_cases(source, phase, asset, source_sha)
    # Registry modes require a valid frozen translation even when the source is a packet.
    if translation_path:
        TranslationAsset.model_validate(asset)
    ensure_local_output(destination)
    if destination.exists():
        raise ValueError("Fresh output directory required; no overwrite")
    destination.mkdir(parents=True)
    storage_key = digest({"source": digest(source), "phase": phase, "renderer": VERSION})
    index = index_html(cases, phase, storage_key)
    review = page_html(cases, phase, storage_key)
    overview = overview_html()
    (destination / "index.html").write_bytes(index)
    (destination / "review.html").write_bytes(review)
    (destination / "overview.html").write_bytes(overview)
    manifest = {
        "renderer_version": VERSION,
        "renderer_source_hash": renderer_hash(),
        "source_json_path": str(source_path),
        "source_json_sha256": source_sha,
        "source_json_canonical_hash": digest(source),
        "translation_asset_path": str(translation_path) if translation_path else None,
        "translation_asset_sha256": file_hash(translation_path) if translation_path else None,
        "translation_versions": sorted({c["translation_version"] for c in cases}),
        "translation_hashes": sorted({c["translation_hash"] for c in cases}),
        "text_lineage_by_case": {c["case_id"]: text_lineage(c) for c in cases},
        "phase": phase,
        "case_aliases": [c["case_id"] for c in cases],
        "html_sha256": {
            "index.html": hashlib.sha256(index).hexdigest(),
            "review.html": hashlib.sha256(review).hexdigest(),
            "overview.html": hashlib.sha256(overview).hexdigest(),
        },
        "read_only_source": True,
        "answer_input_separate_ballot": True,
        "human_review_started": False,
        "final_frozen": False,
    }
    exclusive(destination / "render-manifest.json", manifest)
    return manifest


def renderer_hash():
    paths = [
        HERE / "__init__.py",
        HERE / "renderer.py",
        HERE / "style.css",
        HERE / "stage_tasks.js",
    ]
    paths.extend(
        HERE.parent / name for name in ("schema.py", "bilingual.py", "packets.py", "storage.py")
    )
    paths.extend(
        (
            HERE.parent / "html_display_v1" / "renderer.py",
            HERE.parent / "pilot_materials_v1" / "prepare.py",
            HERE.parent / "codebook.py",
        )
    )
    return digest({p.relative_to(HERE.parent).as_posix(): file_hash(p) for p in paths})


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", required=True)
    p.add_argument("--phase", required=True, choices=PHASES)
    p.add_argument("--destination", required=True)
    p.add_argument("--translations")
    a = p.parse_args()
    result = build(a.source, a.phase, a.destination, a.translations)
    print(
        json.dumps(
            {
                "phase": result["phase"],
                "cases": len(result["case_aliases"]),
                "renderer_version": VERSION,
                "codebook_version": CODEBOOK_VERSION,
                "human_review_started": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
