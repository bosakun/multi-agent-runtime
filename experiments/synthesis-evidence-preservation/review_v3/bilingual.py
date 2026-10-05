"""Display-only frozen bilingual assets. No translator, network or semantic judging."""

import hashlib
from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from review_v3.schema import Record
from review_v3.storage import digest


def text_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class TranslationPair(Record):
    english_original: str = Field(min_length=1)
    japanese_translation: str = Field(min_length=1)
    english_sha256: str
    japanese_sha256: str
    # Author-only references. Do not expose source paths/allocation through packet pairs.
    source_pointers: list[str] = Field(min_length=1)
    display_pointers: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def hashes(self):
        if self.english_sha256 != text_hash(self.english_original) or (
            self.japanese_sha256 != text_hash(self.japanese_translation)
        ):
            raise ValueError("Original/translation text hash mismatch")
        return self


class TranslationAsset(Record):
    version: str = Field(min_length=1)
    review_mode: Literal["pilot", "main"]
    question_id: str
    pairs: list[TranslationPair] = Field(min_length=1)
    preparation_method: str = Field(min_length=1)
    translation_method: Literal[
        "human_manual", "machine_translation", "llm_assisted_translation", "other"
    ]
    translation_prepared_by_or_system: str = Field(min_length=1)
    translation_verified_by: str = Field(min_length=1)
    verification_method: str = Field(min_length=1)
    translation_system_metadata: dict[str, str] = Field(default_factory=dict)
    human_approved_by: str = Field(min_length=1)
    frozen_at: datetime
    frozen_hash: str

    @model_validator(mode="after")
    def frozen(self):
        ids = [(pointer, p.english_sha256) for p in self.pairs for pointer in p.display_pointers]
        if len(set(ids)) != len(ids):
            raise ValueError("One fixed Japanese rendering per source text/display location")
        if digest(self.model_dump(mode="json", exclude={"frozen_hash"})) != self.frozen_hash:
            raise ValueError("Frozen translation asset mutated")
        return self


def display_texts(materials):
    """Collect only source prose already authorized for THIS stage.

    IDs, states, hashes, metadata and human-authored registry annotations are not
    translated. Registry annotations are written in Japanese per the protocol.
    """
    rows = []

    def visit(value, pointer):
        if isinstance(value, str):
            if value:
                rows.append((pointer, value))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                visit(item, f"{pointer}/{i}")
        elif isinstance(value, dict):
            for key, item in value.items():
                if key not in ("evidence_ids", "confidence", "level"):
                    visit(item, f"{pointer}/{key}")

    def sentences(values, prefix):
        for i, sentence in enumerate(values):
            for field in ("title", "text"):
                visit(sentence[field], f"{prefix}/{i}/{field}")

    visit(materials["question_text"], "/question_text")
    sentences(materials["reference_sentences"], "/reference_sentences")
    if "benchmark_alignment" in materials:
        visit(materials["benchmark_alignment"]["gold_answer"], "/benchmark_alignment/gold_answer")
        for i, support in enumerate(materials["benchmark_alignment"]["gold_supporting_facts"]):
            visit(support[0], f"/benchmark_alignment/gold_supporting_facts/{i}/0")
    for i, worker in enumerate(materials.get("workers", [])):
        sentences(worker["actual_input_sentences"], f"/workers/{i}/actual_input_sentences")
        for field in ("public_output", "public_artifact"):
            if field in worker:
                visit(worker[field], f"/workers/{i}/{field}")
    if "actual_synthesizer_input" in materials:
        context = materials["actual_synthesizer_input"]
        for i, artifact in enumerate(context["artifacts"]):
            visit(artifact["payload"], f"/actual_synthesizer_input/artifacts/{i}/payload")
        visit(context["supplementary_material"], "/actual_synthesizer_input/supplementary_material")
    if "final_output" in materials:
        visit(materials["final_output"], "/final_output")
    return rows


def bilingual_projection(materials, asset):
    pairs = {(pointer, p.english_sha256): p for p in asset.pairs for pointer in p.display_pointers}
    visible = []
    for pointer, original in display_texts(materials):
        pair = pairs.get((pointer, text_hash(original)))
        if pair is None or pair.english_original != original:
            raise ValueError(f"Missing fixed Japanese rendering for visible material: {pointer}")
        visible.append(
            {
                "material_pointer": pointer,
                "english_original": pair.english_original,
                "japanese_translation": pair.japanese_translation,
                "english_sha256": pair.english_sha256,
                "japanese_sha256": pair.japanese_sha256,
            }
        )
    return {
        "reviewer_language": "ja",
        "semantic_reference_language": "en",
        "reviewer_primary_display_language": "ja",
        "translation_version": asset.version,
        "pairs": visible,
        "visible_pairs_hash": digest(visible),
    }
