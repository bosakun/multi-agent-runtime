"""Opt-in read-only projection of saved requests. No old runner imports/network."""

import hashlib
import json

from review_v3.packets import ArmSource, WorkerSource, public_output
from review_v3.storage import digest


def text_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def request_context(request):
    if "context" in request:
        return request["context"]
    messages = [m for m in request.get("messages", []) if m["role"] == "user"]
    if len(messages) != 1:
        raise ValueError("Unambiguous serialized user context required")
    return json.loads(messages[0]["content"])


def worker_source(
    worker_id, journal, sentences, intended_ids, artifact_payload, transition_type, source_pointers
):
    """Caller explicitly supplies provenance transition; equality is not semantic retention."""
    if journal.get("error") or not journal.get("response"):
        raise ValueError("Not a successful saved Worker response")
    if journal["agent_id"] != worker_id:
        raise ValueError("Worker journal identity mismatch")
    context = request_context(journal["request"])
    actual = context.get("knowledge")
    ids = None
    if actual is not None:
        mapping = {s.sentence_id: s for s in sentences}
        ids = []
        for item in actual:
            sid = item["id"]
            if sid not in mapping:
                raise ValueError("Actual input contains unregistered raw sentence")
            content = json.loads(item["content"])
            sentence = mapping[sid]
            if (
                content.get("title") != sentence.title
                or content.get("sentence_index") != sentence.sentence_index
                or content.get("text") != sentence.text
                or text_hash(sentence.text) != sentence.text_hash
            ):
                raise ValueError("Actual sentence content differs from reference")
            ids.append(sid)
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate actual sentence ID")
    return WorkerSource(
        worker_id=worker_id,
        actual_sentence_ids=ids,
        intended_sentence_ids=intended_ids,
        public_output=public_output(journal["response"]["output"]),
        public_artifact=public_output(artifact_payload),
        publication_transition_type=transition_type,
        source_pointers={
            **source_pointers,
            "actual_serialized_input_hash": digest(journal["request"]),
        },
    )


def arm_source(request, output, worker_ids, source_pointers):
    context = request_context(request)
    artifacts = context.get("artifacts", [])
    producers = [a["producer"] for a in artifacts]
    if len(producers) != len(set(producers)) or not set(producers) <= set(worker_ids):
        raise ValueError("Ambiguous/unmapped Artifact producers")
    inputs = context.get("inputs", {})
    if not set(inputs) <= {"supplementary_material"}:
        raise ValueError("Unrecognized Synthesizer input route")
    if context.get("knowledge") or context.get("messages"):
        raise ValueError("Unrecognized additional evidence route needs explicit amendment")
    return ArmSource(
        artifacts_by_worker={a["producer"]: public_output(a["payload"]) for a in artifacts},
        supplementary_material=inputs.get("supplementary_material"),
        final_output=public_output(output),
        source_pointers={**source_pointers, "actual_serialized_input_hash": digest(request)},
    )
