"""Versioned stage-only exports. Gold, allocation and future stages stay private."""

import uuid
from pathlib import Path

from pydantic import Field

from review_v3 import BUILDER_VERSION, PROTOCOL_VERSION, RULE_VERSION, SCHEMA_VERSION, STATUS
from review_v3.schema import STAGE_MODELS, Question, Record, Registry, Sentence, Transition
from review_v3.storage import digest, ensure_local_output, exclusive, file_hash


class WorkerSource(Record):
    worker_id: str
    actual_sentence_ids: list[str] | None = None
    intended_sentence_ids: list[str] | None = None
    public_output: dict | None = None
    public_artifact: dict | None = None
    publication_transition_type: Transition = "unknown"
    source_pointers: dict[str, str] = Field(default_factory=dict)


class ArmSource(Record):
    # Author supplies ONLY faithfully projected context, not complete messages/instructions.
    artifacts_by_worker: dict[str, dict] = Field(default_factory=dict)
    supplementary_material: str | None = None
    final_output: dict | None = None
    source_pointers: dict[str, str] = Field(default_factory=dict)


class PrivateSource(Record):
    question: Question
    sentences: list[Sentence]
    workers: list[WorkerSource] = Field(default_factory=list)
    arms: dict[str, ArmSource] = Field(default_factory=dict)
    gold_answer: str | None = None
    gold_supporting_facts: list[list] | None = None
    condition_mapping: dict = Field(default_factory=dict)
    automated_scores: dict = Field(default_factory=dict)
    aggregate_outcomes: dict = Field(default_factory=dict)
    source_hashes: dict[str, str] = Field(default_factory=dict)


PUBLIC_KEYS = {
    "candidate_answer",
    "findings",
    "text",
    "evidence_ids",
    "uncertainty",
    "answer",
    "reason",
    "confidence",
    "level",
    "message",
    "assumptions",
    "unknowns",
}


def public_output(value):
    """Reject unknown metadata instead of silently exporting a whole trace.

    Does not redact evidence prose/output content, which must remain faithful.
    Natural content/structure can reveal allocation; this is not full blinding.
    """
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [public_output(v) for v in value]
    if not isinstance(value, dict) or not set(value) <= PUBLIC_KEYS:
        raise ValueError("Unexpected private/condition/score field in public output")
    return {key: public_output(v) for key, v in value.items()}


def blank_registry(source, phase):
    # Raw sentences are reference materials, never AI-discovered facts/paths.
    registry = Registry(question=source.question, sentences=source.sentences)
    return {
        "phase": phase,
        "registry": registry.model_dump(mode="json"),
        "provenance": {
            "reviewer_id": None,
            "rationale": None,
            "timestamp": None,
            "registry_phase": phase,
            "judgment_status": None,
        },
    }


def blank_stage(registry, phase, arm=None, worker_ids=()):
    phases = ["S5a", "S5b"] if phase == "S5" else [phase]
    forms = []
    for stage in phases:
        # Unit creation happens from HUMAN-FROZEN registry, not AI fact discovery.
        if stage == "S5b":
            units = [(None, p.path_id, None) for p in registry.paths if p.validity == "yes"]
        else:
            workers = worker_ids if stage in ("S1", "S2", "S3", "S4") else [None]
            units = [(f.fact_id, None, worker) for f in registry.facts for worker in workers]
        for fact, path, worker in units:
            forms.append(
                {
                    "stage": stage,
                    "annotation": STAGE_MODELS[stage](
                        question_id=registry.question.question_id,
                        fact_id=fact,
                        path_id=path,
                        worker_id=worker,
                        arm=arm if stage in ("S4", "S5a", "S5b") else None,
                    ).model_dump(mode="json"),
                }
            )
    return forms


def project(source, registry, phase, selected_arm, aliases):
    sentence_map = {s.sentence_id: s.model_dump(mode="json") for s in source.sentences}
    base = {
        "question_text": source.question.question_text,
        "reference_sentences": list(sentence_map.values()),
    }
    if phase in ("R1", "R2"):
        if phase == "R2":
            if source.gold_answer is None or source.gold_supporting_facts is None:
                raise ValueError("Missing R2 alignment material")
            base["benchmark_alignment"] = {
                "gold_answer": source.gold_answer,
                "gold_supporting_facts": source.gold_supporting_facts,
            }
        return base
    base["registry_projection"] = registry.model_dump(mode="json", exclude={"frozen_hash"})
    base["registry_origin_hash"] = registry.frozen_hash
    # Strip author provenance: real reviewer identity, source paths, original question ID.
    base["registry_projection"]["question"]["question_id"] = aliases["question"]
    base["registry_projection"]["judgments"] = []
    for member in base["registry_projection"]["memberships"]:
        member["question_id"] = aliases["question"]
    base["registry_projection_hash"] = digest(base["registry_projection"])
    workers = []
    for worker in source.workers:
        row = {
            "worker": aliases[worker.worker_id],
            "actual_input_available": worker.actual_sentence_ids is not None,
            "actual_input_sentences": [
                sentence_map[sid] for sid in worker.actual_sentence_ids or []
            ],
        }
        if phase != "S1":
            row["public_output"] = public_output(worker.public_output)
        if phase in ("S3", "S4", "S5"):
            row["publication_transition_type"] = worker.publication_transition_type
            row["public_artifact"] = public_output(worker.public_artifact)
        workers.append(row)
    base["workers"] = workers
    if phase in ("S4", "S5"):
        if selected_arm not in source.arms:
            raise ValueError("Explicit author-side arm selection required")
        arm = source.arms[selected_arm]
        base["actual_synthesizer_input"] = {
            "artifacts": [
                {"producer": aliases[w], "payload": public_output(payload)}
                for w, payload in arm.artifacts_by_worker.items()
            ],
            "supplementary_material": arm.supplementary_material,
        }
        if phase == "S5":
            base["final_output"] = public_output(arm.final_output)
    return base


def build_packet(
    source,
    workflow,
    registry,
    phase,
    reviewer,
    destination,
    selected_arm=None,
    case_alias=None,
    arm_alias=None,
    scope=None,
):
    """Export ONE authorized stage; never build all future stages at once.

    Author-side source is private. Output destination must be a fresh local folder.
    Semantic form fields are blank, even where a machine provenance rule exists.
    """
    workflow.authorize(phase, reviewer)
    if scope is None or source.question.question_id not in scope.included_case_ids:
        raise ValueError("Explicit human case inclusion manifest required")
    if phase not in ("R1", "R2"):
        workflow.verify_registry(registry)
    allowed_registry_ids = {source.question.question_id}
    if phase == "R2" and case_alias:
        allowed_registry_ids.add(case_alias)  # This reviewer's immutable anonymous R1 ballot.
    if (
        registry.question.question_id not in allowed_registry_ids
        or registry.question.question_text != source.question.question_text
        or registry.question.source_hash != source.question.source_hash
    ):
        raise ValueError("Source/registry question mismatch")
    for worker in source.workers:
        known = {s.sentence_id for s in source.sentences}
        if worker.actual_sentence_ids is not None and not set(worker.actual_sentence_ids) <= known:
            raise ValueError("Unknown actual input sentence")
    aliases = {
        "question": case_alias or "case-" + uuid.uuid4().hex,
        "arm": arm_alias or "response-" + uuid.uuid4().hex,
        **{w.worker_id: f"worker-{i + 1}" for i, w in enumerate(source.workers)},
    }
    packet = {
        "case_code": aliases["question"],
        "phase": phase,
        "allocation_blinding": "allocation-blinded where feasible",
        "materials": project(source, registry, phase, selected_arm, aliases),
        "form": blank_registry(source, phase)
        if phase in ("R1", "R2")
        else blank_stage(
            registry, phase, aliases["arm"], [aliases[w.worker_id] for w in source.workers]
        ),
    }
    if phase == "R2":
        lock = next(
            item for item in workflow.locks if item.phase == "R1" and item.reviewer_id == reviewer
        )
        if digest(registry.model_dump(mode="json")) != lock.content_hash:
            raise ValueError("R2 requires THIS reviewer's immutable R1 registry")
        packet["materials"]["own_locked_R1_registry"] = registry.model_dump(mode="json")
        packet["materials"]["own_locked_R1_registry"]["question"]["question_id"] = aliases[
            "question"
        ]
    if phase in ("R1", "R2"):
        packet["form"]["registry"]["question"]["question_id"] = aliases["question"]
    else:
        for form in packet["form"]:
            form["annotation"]["question_id"] = aliases["question"]
    destination = Path(destination)
    ensure_local_output(destination)
    destination.mkdir(parents=True, exist_ok=False)
    packet_hash = exclusive(destination / "packet.json", packet)
    manifest = {
        "protocol_version": PROTOCOL_VERSION,
        "schema_version": SCHEMA_VERSION,
        "codebook_version": workflow.codebook_version,
        "builder_version": BUILDER_VERSION,
        "analysis_rule_version": RULE_VERSION,
        "status": STATUS,
        "packet_hashes": {"packet.json": packet_hash},
        # Source path mapping, gold timing, scores, and allocations are coordinator-only.
        "visible_materials_hash": digest(packet["materials"]),
        "registry_hash": workflow.registry_hash,
        "codebook_hash": workflow.codebook_hash,
        "phase": phase,
        "gold_included": phase == "R2",
        "condition_mapping_included": False,
        "scores_included": False,
    }
    exclusive(destination / "manifest.json", manifest)
    manifest_hash = file_hash(destination / "manifest.json")
    return {
        "packet_manifest_hash": manifest_hash,
        "private_linkage": {
            "question_id": source.question.question_id,
            "arm": selected_arm,
            "reviewer": reviewer,
            "aliases": aliases,
            "source_hashes": source.source_hashes,
            "private_source_bundle_hash": digest(source.model_dump(mode="json")),
            "packet_manifest_hash": manifest_hash,
            "protocol_version": PROTOCOL_VERSION,
            "schema_version": SCHEMA_VERSION,
            "builder_version": BUILDER_VERSION,
            "analysis_rule_version": RULE_VERSION,
        },
        "packet": packet,
    }
