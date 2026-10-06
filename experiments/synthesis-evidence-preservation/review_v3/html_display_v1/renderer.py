"""No network, translator, labels or authorization; one phase per output directory."""

import argparse
import hashlib
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from review_v3.bilingual import (  # noqa: E402
    TranslationAsset,
    bilingual_projection,
    text_hash,
)
from review_v3.packets import public_output  # noqa: E402
from review_v3.pilot_materials_v1.prepare import MARKER  # noqa: E402
from review_v3.pilot_materials_v1.prepare import VERSION as MATERIAL_VERSION
from review_v3.schema import Registry, Sentence  # noqa: E402
from review_v3.storage import (  # noqa: E402
    digest,
    ensure_local_output,
    exclusive,
    file_hash,
    read,
    safe_id,
)

VERSION = "static-html-display-v1.0.0"
PHASES = ("R1", "R2", "S1", "S2", "S3", "S4", "S5")
HERE = Path(__file__).resolve().parent


def fields(value, allowed, required=()):
    if not isinstance(value, dict) or set(value) - set(allowed) or set(required) - set(value):
        raise ValueError("Unexpected, future-stage or missing JSON field")


def pointer_get(value, pointer):
    for segment in pointer.lstrip("/").split("/"):
        segment = segment.replace("~1", "/").replace("~0", "~")
        value = value[int(segment)] if isinstance(value, list) else value[segment]
    return value


def pointer_key(key):
    return str(key).replace("~", "~0").replace("/", "~1")


def check_bilingual(value):
    fields(value, {"en", "ja"}, {"en", "ja"})
    if not all(isinstance(value[k], str) and value[k] for k in ("en", "ja")):
        raise ValueError("Existing English and Japanese text required")


def id_list(values):
    if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
        raise ValueError("IDs must be a list of strings, not nested private objects")
    for value in values:
        safe_id(value)


def worker_map(values, bilingual=False):
    if not isinstance(values, dict):
        raise ValueError("Worker mapping required")
    for worker, value in values.items():
        if not worker.startswith("w") or not worker[1:].isdigit():
            raise ValueError("Prepared synthetic worker IDs must be w1, w2, ...")
        check_bilingual(value) if bilingual else id_list(value)


def validate_b(case, phase):
    allowed = {
        "marker",
        "vignette_id",
        "phase",
        "question",
        "reference",
        "teaching_reference",
        "actual_worker_input_sentence_ids",
        "exercise_prompt_ja",
    }
    if phase != "S1":
        allowed.add("worker_public_expression")
    if phase in {"S3", "S4", "S5"}:
        allowed.update({"publication_transition_type", "published_artifact"})
    if phase in {"S4", "S5"}:
        allowed.add("actual_synthesizer_input")
    if phase == "S5":
        allowed.add("final_output")
    fields(case, allowed, allowed)
    if phase not in PHASES[2:] or case["phase"] != phase or case["marker"] != MARKER:
        raise ValueError("Explicit synthetic, single-stage source required")
    safe_id(case["vignette_id"])
    check_bilingual(case["question"])
    worker_map(case["actual_worker_input_sentence_ids"])
    for sentence in case["reference"]:
        fields(sentence, {"sentence_id", "text"}, {"sentence_id", "text"})
        check_bilingual(sentence["text"])
    teaching = case["teaching_reference"]
    fields(
        teaching, {"marker", "facts", "support_sets", "paths"}, {"facts", "support_sets", "paths"}
    )
    for fact in teaching["facts"]:
        fields(fact, {"fact_id", "text"}, {"fact_id", "text"})
        check_bilingual(fact["text"])
        safe_id(fact["fact_id"])
    for support in teaching["support_sets"]:
        fields(
            support,
            {"support_set_id", "fact_id", "evidence_sentence_ids"},
            {"support_set_id", "fact_id", "evidence_sentence_ids"},
        )
        safe_id(support["support_set_id"])
        safe_id(support["fact_id"])
        id_list(support["evidence_sentence_ids"])
    for path in teaching["paths"]:
        fields(
            path,
            {"path_id", "required_fact_ids", "support_set_ids", "proposed_external_premise"},
            {"path_id", "required_fact_ids"},
        )
        safe_id(path["path_id"])
        id_list(path["required_fact_ids"])
        if "support_set_ids" in path:
            id_list(path["support_set_ids"])
        if "proposed_external_premise" in path:
            check_bilingual(path["proposed_external_premise"])
    for name in ("worker_public_expression", "published_artifact"):
        worker_map(case.get(name, {}), bilingual=True)
    if "publication_transition_type" in case and case["publication_transition_type"] not in {
        "separate_records",
        "identity_alias",
        "unknown",
    }:
        raise ValueError("Unknown publication transition type")
    if "actual_synthesizer_input" in case:
        context = case["actual_synthesizer_input"]
        fields(
            context,
            {"artifacts", "supplementary_evidence"},
            {"artifacts", "supplementary_evidence"},
        )
        worker_map(context["artifacts"], bilingual=True)
        for value in context["supplementary_evidence"]:
            check_bilingual(value)
    if "final_output" in case:
        check_bilingual(case["final_output"])


def validate_a(material, phase):
    allowed = {"case_alias", "question", "reference_sentences"}
    if phase == "R2":
        allowed.add("benchmark_alignment")
    fields(material, allowed, allowed)
    safe_id(material["case_alias"])
    if phase not in {"R1", "R2"}:
        raise ValueError("Prepared Pilot A is R1/R2 only")
    for sentence in material["reference_sentences"]:
        fields(
            sentence,
            {"sentence_id", "title", "sentence_index", "sentence_text"},
            {"sentence_id", "title", "sentence_index", "sentence_text"},
        )
    if phase == "R2":
        validate_gold(material["benchmark_alignment"])


def validate_gold(gold):
    fields(gold, {"gold_answer", "gold_supporting_facts"}, {"gold_answer", "gold_supporting_facts"})
    if not isinstance(gold["gold_answer"], str):
        raise ValueError("Gold answer must be original text")
    for support in gold["gold_supporting_facts"]:
        if len(support) != 2 or not isinstance(support[0], str) or not isinstance(support[1], int):
            raise ValueError("Expected original title and sentence index")


def validate_packet(packet, phase):
    fields(
        packet,
        {
            "case_code",
            "phase",
            "review_mode",
            "allocation_blinding",
            "materials",
            "form",
            "bilingual_display",
        },
        {"case_code", "phase", "materials", "bilingual_display"},
    )
    if phase not in PHASES or packet["phase"] != phase:
        raise ValueError("Packet/phase mismatch")
    safe_id(packet["case_code"])
    allowed = {"question_text", "reference_sentences"}
    required = allowed.copy()
    if phase == "R2":
        allowed.update({"benchmark_alignment", "own_locked_R1_registry"})
        required.add("benchmark_alignment")
    if phase in PHASES[2:]:
        allowed.update(
            {"registry_projection", "registry_origin_hash", "registry_projection_hash", "workers"}
        )
        required.update({"registry_projection", "workers"})
    if phase in {"S4", "S5"}:
        allowed.add("actual_synthesizer_input")
        required.add("actual_synthesizer_input")
    if phase == "S5":
        allowed.add("final_output")
        required.add("final_output")
    materials = packet["materials"]
    fields(materials, allowed, required)
    for sentence in materials["reference_sentences"]:
        Sentence.model_validate(sentence)
    if "benchmark_alignment" in materials:
        validate_gold(materials["benchmark_alignment"])
    for key in ("registry_projection", "own_locked_R1_registry"):
        if key in materials:
            Registry.model_validate(materials[key])
    for worker in materials.get("workers", []):
        worker_allowed = {"worker", "actual_input_available", "actual_input_sentences"}
        if phase != "S1":
            worker_allowed.add("public_output")
        if phase in {"S3", "S4", "S5"}:
            worker_allowed.update({"publication_transition_type", "public_artifact"})
        fields(worker, worker_allowed, worker_allowed)
        for sentence in worker["actual_input_sentences"]:
            Sentence.model_validate(sentence)
        for key in ("public_output", "public_artifact"):
            if key in worker:
                public_output(worker[key])
    if "actual_synthesizer_input" in materials:
        context = materials["actual_synthesizer_input"]
        fields(
            context,
            {"artifacts", "supplementary_material"},
            {"artifacts", "supplementary_material"},
        )
        for artifact in context["artifacts"]:
            fields(artifact, {"producer", "payload"}, {"producer", "payload"})
            public_output(artifact["payload"])
    if "final_output" in materials:
        public_output(materials["final_output"])


class Display:
    def __init__(self, source, asset=None, pairs=None, prefix=""):
        self.source = source
        self.asset = asset
        self.pairs = pairs or {}
        self.prefix = prefix
        self.lineage = []

    def pair(self, en, ja, pointer, translation_pointer, source_pointers=None):
        self.lineage.append(
            dict(
                source_pointer=self.prefix + pointer,
                translation_pointer=translation_pointer,
                english_sha256=text_hash(en),
                japanese_sha256=text_hash(ja),
                author_source_pointers=source_pointers or [],
            )
        )
        return (
            '<div class="pair"><div class="ja"><span class="label">日本語</span>'
            f'<div class="text" lang="ja">{html.escape(ja)}</div></div>'
            '<div class="en"><span class="label">English original</span>'
            f'<div class="text" lang="en">{html.escape(en)}</div></div></div>'
        )

    def prose(self, value, pointer):
        if value == "":
            return self.pair("", "", pointer, None)
        pair = self.pairs.get(pointer)
        if pair is None or pair[1].english_original != value:
            raise ValueError("Missing fixed Japanese translation for visible source text")
        i, p = pair
        return self.pair(
            value,
            p.japanese_translation,
            pointer,
            f"translation_asset/pairs/{i}/japanese_translation",
            p.source_pointers,
        )

    def value(self, value, pointer, translated=True):
        if isinstance(value, dict):
            if set(value) == {"en", "ja"}:
                return self.pair(
                    value["en"], value["ja"], pointer + "/en", self.prefix + pointer + "/ja"
                )
            chunks = []
            for key in sorted(value):
                child = pointer + "/" + pointer_key(key)
                child_translated = translated and key not in {"evidence_ids", "confidence", "level"}
                child_html = self.value(value[key], child, child_translated)
                chunks.append(
                    f"<h3>{html.escape(LABELS.get(key, key))}</h3>"
                    f'<div class="structure">{child_html}</div>'
                )
            return "".join(chunks)
        if isinstance(value, list):
            return "".join(
                f'<div class="sentence">{self.value(v, pointer + "/" + str(i), translated)}</div>'
                for i, v in enumerate(value)
            )
        if isinstance(value, str) and value and translated:
            return self.prose(value, pointer)
        text = str(value) if value is not None else "（記録なし）"
        return f'<div class="text">{html.escape(text)}</div>'


LABELS = {
    "facts": "登録された事実（教材・Registry）",
    "fact_id": "事実ID",
    "text": "文章",
    "support_sets": "証拠の組",
    "support_set_id": "証拠の組ID",
    "evidence_sentence_ids": "証拠sentence IDs",
    "paths": "回答を支持する道筋",
    "path_id": "道筋ID",
    "required_fact_ids": "道筋に必要な事実ID",
    "support_set_ids": "証拠の組IDs",
    "proposed_external_premise": "提示された外部前提",
    "candidate_answer": "候補回答",
    "findings": "公開された記述",
    "evidence_ids": "引用IDs",
    "uncertainty": "不確実性の記述",
    "answer": "回答",
    "reason": "理由の記述",
    "artifacts": "Artifact経路",
    "supplementary_evidence": "追加原文の経路",
}


def card(title, body, question=False):
    cls = "card question" if question else "card"
    return f'<section class="{cls}"><h2>{html.escape(title)}</h2>{body}</section>'


def document(case_id, phase, body, synthetic):
    warning = (
        "この段階ではGold Answer、Worker Output、Final Answer等は参照しない。"
        if phase == "R1"
        else "この段階で許可された資料だけを参照してください。"
    )
    marker = f'<div class="warning">{html.escape(MARKER)}</div>' if synthetic else ""
    return (
        '<!doctype html>\n<html lang="ja"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; '
        "style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'\">"
        f"<title>{html.escape(case_id)} · {phase}</title><style>"
        + (HERE / "style.css").read_text(encoding="utf-8")
        + "</style></head><body><main>"
        f'<header><span class="badge">{phase}</span> <span class="id">{html.escape(case_id)}</span>'
        '<h1>Human Review · 表示用資料</h1><div class="warning">'
        "READ-ONLY / PREPARATION DISPLAY — 人間review開始の認可ではありません。"
        f"<br>{warning}</div>{marker}</header>{body}"
        "<footer>意味のreferenceは英語原文です。訳の曖昧さは担当者へ記録してください。"
        f"<br>静的表示版：{VERSION}。判定票は既存の別templateを使用します。"
        "</footer></main></body></html>\n"
    ).encode("utf-8")


def asset_pairs(asset):
    return {p: (i, pair) for i, pair in enumerate(asset.pairs) for p in pair.display_pointers}


def evidence(display, sentences, pointer, text_field="text"):
    groups = {}
    for i, sentence in enumerate(sentences):
        groups.setdefault(sentence["title"], []).append((i, sentence))
    chunks = []
    for title, group in groups.items():
        i = group[0][0]
        if (
            len({display.pairs[f"{pointer}/{j}/title"][1].japanese_translation for j, _ in group})
            != 1
        ):
            raise ValueError("Repeated document title has inconsistent fixed translations")
        title_html = display.prose(title, f"{pointer}/{i}/title")
        body = title_html
        for i, sentence in group:
            body += (
                '<div class="sentence"><span class="id">'
                + html.escape(sentence["sentence_id"])
                + "</span>"
                + display.prose(sentence[text_field], f"{pointer}/{i}/{text_field}")
                + "</div>"
            )
        chunks.append(card("Reference evidence · 文書", body))
    return "".join(chunks)


def render(source, phase, translations=None):
    if phase not in PHASES:
        raise ValueError("Known phase required")
    synthetic = "vignette_id" in source
    prepared_a = "case_alias" in source
    if synthetic:
        validate_b(source, phase)
        case_id = source["vignette_id"]
        d = Display(source)
        body = card("Question · 質問", d.value(source["question"], "/question"), True)
        for i, sentence in enumerate(source["reference"]):
            body += card(
                "Reference evidence · " + sentence["sentence_id"],
                d.value(sentence["text"], f"/reference/{i}/text"),
            )
        # These are supplied teaching premises, not reviewer answer keys or new annotations.
        body += card(
            "人工教材の参照定義",
            d.value(source["teaching_reference"], "/teaching_reference", False),
        )
        body += card(
            "S1 · Workerに実際に渡ったsentence IDs",
            d.value(
                source["actual_worker_input_sentence_ids"],
                "/actual_worker_input_sentence_ids",
                False,
            ),
        )
        for key, title in (
            ("worker_public_expression", "S2 · Worker public expression"),
            ("publication_transition_type", "S3 · 公開遷移の種類"),
            ("published_artifact", "S3 · 公開Artifact"),
            ("actual_synthesizer_input", "S4 · 実Synthesizer入力"),
            ("final_output", "S5 · 最終出力"),
        ):
            if key in source:
                body += card(title, d.value(source[key], "/" + key, False))
        body += card(
            "練習の案内", d.value(source["exercise_prompt_ja"], "/exercise_prompt_ja", False)
        )
        translation_meta = dict(
            translation_asset_version=MATERIAL_VERSION,
            translation_asset_hash=digest(
                [{k: row[k] for k in ("english_sha256", "japanese_sha256")} for row in d.lineage]
            ),
            translation_basis="synthetic embedded English/Japanese",
            human_translation_frozen=False,
        )
    else:
        if translations is None:
            raise ValueError(
                "Fixed Japanese TranslationAsset required; no translation is generated"
            )
        asset = TranslationAsset.model_validate(
            translations.model_dump(mode="json")
            if isinstance(translations, TranslationAsset)
            else translations
        )
        if prepared_a:
            validate_a(source, phase)
            if asset.review_mode != "pilot":
                raise ValueError("Pilot A requires pilot translation asset")
            materials, case_id, question_field, text_field = (
                source,
                source["case_alias"],
                "question",
                "sentence_text",
            )
        else:
            validate_packet(source, phase)
            if asset.review_mode != source.get("review_mode", "pilot"):
                raise ValueError("Packet/translation review mode mismatch")
            materials, case_id, question_field, text_field = (
                source["materials"],
                source["case_code"],
                "question_text",
                "text",
            )
            if source["bilingual_display"] != bilingual_projection(materials, asset):
                raise ValueError("Packet bilingual projection differs from supplied fixed asset")
        d = Display(materials, asset, asset_pairs(asset), "" if prepared_a else "/materials")
        body = card(
            "Question · 質問", d.prose(materials[question_field], "/" + question_field), True
        )
        body += evidence(d, materials["reference_sentences"], "/reference_sentences", text_field)
        if phase == "R2":
            gold = materials["benchmark_alignment"]
            body += card(
                "Gold Answer · benchmark alignment",
                d.prose(gold["gold_answer"], "/benchmark_alignment/gold_answer"),
            )
            supports = ""
            for i, support in enumerate(gold["gold_supporting_facts"]):
                supports += d.prose(support[0], f"/benchmark_alignment/gold_supporting_facts/{i}/0")
                supports += f'<div class="id">sentence index: {support[1]}</div>'
            body += card("Gold Supporting Facts", supports)
        # R2's own locked ballot is a separate personal annotation record. Keeping
        # it out of shared material HTML lets both reviewers receive identical bytes.
        for key in ("registry_projection",):
            if key in materials:
                reg = materials[key]
                body += card(
                    "人間のRegistry · " + key,
                    d.value(
                        {k: reg[k] for k in ("facts", "support_sets", "paths", "memberships")},
                        "/" + key,
                        False,
                    ),
                )
        for i, worker in enumerate(materials.get("workers", [])):
            prefix = f"/workers/{i}"
            body += card(
                "S1 · " + worker["worker"],
                evidence(d, worker["actual_input_sentences"], prefix + "/actual_input_sentences"),
            )
            if not worker["actual_input_available"]:
                body += card("入力記録", "actual input record: missing")
            for key, title in (
                ("public_output", "S2 · Worker公開出力"),
                ("public_artifact", "S3 · Artifact"),
            ):
                if key in worker:
                    body += card(title, d.value(worker[key], prefix + "/" + key))
            if "publication_transition_type" in worker:
                body += card("S3 · 遷移の種類", html.escape(worker["publication_transition_type"]))
        if "actual_synthesizer_input" in materials:
            context = materials["actual_synthesizer_input"]
            for i, artifact in enumerate(context["artifacts"]):
                body += card(
                    "S4 · Artifact経路 · " + artifact["producer"],
                    d.value(
                        artifact["payload"], f"/actual_synthesizer_input/artifacts/{i}/payload"
                    ),
                )
            body += card(
                "S4 · 追加原文の経路",
                d.value(
                    context["supplementary_material"],
                    "/actual_synthesizer_input/supplementary_material",
                ),
            )
        if "final_output" in materials:
            body += card("S5 · 最終出力", d.value(materials["final_output"], "/final_output"))
        translation_meta = dict(
            translation_asset_version=asset.version,
            translation_asset_hash=asset.frozen_hash,
            translation_basis="existing fixed TranslationAsset",
            translation_hash_valid=True,
        )
    return case_id, document(case_id, phase, body, synthetic), d.lineage, translation_meta


def renderer_hash():
    sources = [HERE / "renderer.py", HERE / "style.css"]
    sources += [
        HERE.parent / name for name in ("storage.py", "bilingual.py", "packets.py", "schema.py")
    ]
    return digest({p.relative_to(HERE.parent).as_posix(): file_hash(p) for p in sources})


def build(source_path, phase, destination, translation_path=None):
    source_path, destination = Path(source_path), Path(destination)
    value = read(source_path)
    units = value if isinstance(value, list) else [value]
    if not units:
        raise ValueError("Nonempty stage source required")
    asset = read(translation_path) if translation_path else None
    # Validate every unit before any output: no partial bundle on bad input.
    rendered = [render(unit, phase, asset) for unit in units]
    if len({row[0] for row in rendered}) != len(rendered):
        raise ValueError("Duplicate case/vignette ID")
    ensure_local_output(destination)
    if destination.exists():
        raise ValueError("Fresh output directory required; no overwrite")
    destination.mkdir(parents=True)
    entries = []
    for i, (case_id, data, lineage, metadata) in enumerate(rendered):
        filename = safe_id(case_id) + ".html"
        (destination / filename).write_bytes(data)
        if isinstance(value, list):
            for entry in lineage:
                entry["source_pointer"] = f"/{i}" + entry["source_pointer"]
                if entry["translation_pointer"] and entry["translation_pointer"].startswith("/"):
                    entry["translation_pointer"] = f"/{i}" + entry["translation_pointer"]
        entries.append(
            dict(
                case_id=case_id,
                phase=phase,
                html_file=filename,
                html_sha256=hashlib.sha256(data).hexdigest(),
                source_pointer=f"/{i}" if isinstance(value, list) else "",
                text_lineage=lineage,
                **metadata,
            )
        )
    index_body = (
        '<section class="card"><h2>この段階の資料</h2><ul>'
        + "".join(
            f'<li><a href="{e["html_file"]}">{html.escape(e["case_id"])}</a></li>' for e in entries
        )
        + "</ul></section>"
    )
    index = document("phase index", phase, index_body, all("vignette_id" in u for u in units))
    (destination / "index.html").write_bytes(index)
    manifest = dict(
        renderer_version=VERSION,
        renderer_source_hash=renderer_hash(),
        source_json_path=str(source_path),
        source_json_sha256=file_hash(source_path),
        source_json_canonical_hash=digest(value),
        phase=phase,
        translation_json_path=str(translation_path) if translation_path else None,
        translation_json_sha256=file_hash(translation_path) if translation_path else None,
        index_html_sha256=hashlib.sha256(index).hexdigest(),
        entries=entries,
        read_only=True,
        human_review_started=False,
        final_frozen=False,
        manifest_visibility="coordinator-only: paths and author source pointers",
    )
    exclusive(destination / "render-manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--phase", required=True, choices=PHASES)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--translations")
    args = parser.parse_args()
    result = build(args.source, args.phase, args.destination, args.translations)
    print(
        json.dumps(
            {
                "phase": result["phase"],
                "html_files": len(result["entries"]),
                "renderer_version": VERSION,
                "human_review_started": False,
            },
            indent=2,
        )
    )
