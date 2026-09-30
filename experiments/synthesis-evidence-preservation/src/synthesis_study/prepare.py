"""Create gold-blind fixed-worker inputs and deterministic token-length controls."""

import hashlib
import json
from typing import Any

from bounded_pilot.contract import bounded_schema
from native_pilot.provider import native_body
from pydantic import BaseModel, ConfigDict

from synthesis_study.io import STUDY, digest, exclusive
from synthesis_study.source import Sources


class SupplementaryInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    supplementary_material: str


def request_body(source: Sources, qid: str, supplement: str) -> dict[str, Any]:
    request = source.request(qid).model_copy(deep=True)
    request.instruction = source.spec["common_instruction"]
    request.context.inputs = SupplementaryInput(supplementary_material=supplement).model_dump()
    request.output_schema = bounded_schema(request.output_schema, request.context)
    return native_body(request)


def control_text(tokenizer: Any, target: int) -> str:
    if target == 0:
        return ""
    words = (STUDY / "assets/length-control.txt").read_text(encoding="utf-8").split()
    repeat = 1
    while tokenizer.count(" ".join(words * repeat)) < target + 8:
        repeat *= 2
    expanded = words * repeat
    # Count all candidates in a native batch; exact minimum with deterministic tie-break.
    candidates = [" ".join(expanded[:length]) for length in range(1, len(expanded) + 1)]
    encodings = tokenizer.tokenizer.encode_batch(candidates, add_special_tokens=False)
    index = min(
        range(len(candidates)),
        key=lambda i: (abs(len(encodings[i].ids) - target), len(encodings[i].ids), i),
    )
    return candidates[index]


def make_inputs(source: Sources, tokenizer: Any, *, enforce_limits: bool = True) -> dict[str, Any]:
    verification = source.verify_tokenizer(tokenizer)
    if verification["max_absolute_difference"] != 0:
        raise ValueError("Tokenizer does not exactly reproduce saved native prompt counts")
    if tokenizer.identity["manifest_sha256"] != source.spec["generation"]["model_digest"]:
        raise ValueError("Installed model digest drift")
    inputs, counts, failures = {}, [], []
    qids = list(dict.fromkeys(source.spec["smoke_question_ids"] + source.spec["main_question_ids"]))
    for qid in qids:
        text, ids = source.excerpt(qid)
        b_tokens = tokenizer.count(text)
        control = control_text(tokenizer, b_tokens)
        for arm, supplement in [("A", ""), ("B", text), ("C", control)]:
            body = request_body(source, qid, supplement)
            token_count = tokenizer.prompt_count(body)
            inputs[qid, arm] = {
                "qid": qid,
                "arm": arm,
                "body": body,
                "body_sha256": digest(body),
                "prompt_tokens": token_count,
                "supplement_tokens": tokenizer.count(supplement),
                "allowed_ids": ids,
                "worker_payload_hashes": [
                    digest(a.payload) for a in source.request(qid).context.artifacts
                ],
            }
            counts.append(
                {
                    "qid": qid,
                    "arm": arm,
                    "prompt_tokens": token_count,
                    "supplement_tokens": tokenizer.count(supplement),
                }
            )
            if token_count > source.spec["generation"]["input_token_limit"]:
                failures.append(
                    {"qid": qid, "arm": arm, "prompt_tokens": token_count, "reason": "input_cap"}
                )
        b, c = inputs[qid, "B"], inputs[qid, "C"]
        for key in ["prompt_tokens", "supplement_tokens"]:
            if abs(b[key] - c[key]) > max(1, b[key] * 0.05):
                failures.append({"qid": qid, "reason": "token_matching", "field": key})
    plan = []
    for phase, selected in [
        ("smoke", source.spec["smoke_question_ids"]),
        ("main", source.spec["main_question_ids"]),
    ]:
        for qid in selected:
            arms = sorted(
                source.spec["arms"],
                key=lambda arm: hashlib.sha256(
                    f"20260930:{phase}:{qid}:{arm}".encode()
                ).hexdigest(),
            )
            for arm in arms:
                plan.append({"phase": phase, **inputs[qid, arm]})
    if len(plan) != 81 or len({(item["phase"], item["qid"], item["arm"]) for item in plan}) != 81:
        raise ValueError("Expected exactly 81 distinct planned cells")
    result = {
        "spec": source.spec,
        "tokenizer": tokenizer.exported(),
        "tokenizer_verification": verification,
        "source_hashes": source.hashes,
        "calls": plan,
        "token_counts": counts,
        "failures": failures,
        "maximum_prompt_tokens": max(row["prompt_tokens"] for row in counts),
    }
    if enforce_limits and failures:
        raise ValueError(
            f"Preparation gate failed: {len(failures)} inputs; "
            f"max {result['maximum_prompt_tokens']} tokens"
        )
    return result


def save_inputs(value: dict[str, Any]) -> None:
    if value["failures"]:
        exclusive(
            STUDY / "reports/input-feasibility.json",
            {key: item for key, item in value.items() if key not in {"calls", "source_hashes"}},
        )
        raise ValueError("Input feasibility failed; plan amendment required before generation")
    exclusive(STUDY / "data/replay-inputs/manifest.json", value)


def validate_manifest(value: dict[str, Any]) -> None:
    source = Sources()
    if value["spec"] != source.spec or value["source_hashes"] != source.hashes or value["failures"]:
        raise ValueError("Prepared inputs do not match current immutable sources")
    control_words = (STUDY / "assets/length-control.txt").read_text(encoding="utf-8").split()
    expected_order = []
    for phase, ids in [
        ("smoke", source.spec["smoke_question_ids"]),
        ("main", source.spec["main_question_ids"]),
    ]:
        for qid in ids:
            arms = sorted(
                source.spec["arms"],
                key=lambda arm: hashlib.sha256(
                    f"20260930:{phase}:{qid}:{arm}".encode()
                ).hexdigest(),
            )
            expected_order.extend((phase, qid, arm) for arm in arms)
    if [(p["phase"], p["qid"], p["arm"]) for p in value["calls"]] != expected_order:
        raise ValueError("Prepared question/condition order differs from specification")
    for planned in value["calls"]:
        context = json.loads(planned["body"]["messages"][1]["content"])
        supplement = SupplementaryInput.model_validate(context["inputs"]).supplementary_material
        expected_excerpt, ids = source.excerpt(planned["qid"])
        if planned["arm"] == "A" and supplement:
            raise ValueError("Baseline contains supplementary data")
        if planned["arm"] == "B" and supplement != expected_excerpt:
            raise ValueError("Excerpt differs from annotation-blind worker citations")
        if planned["arm"] == "C":
            words = supplement.split()
            if (
                any(word != control_words[i % len(control_words)] for i, word in enumerate(words))
                or " ".join(words) != supplement
            ):
                raise ValueError("Control contains data outside the fixed neutral passage")
        if (
            planned["allowed_ids"] != ids
            or planned["body"] != request_body(source, planned["qid"], supplement)
            or digest(planned["body"]) != planned["body_sha256"]
        ):
            raise ValueError("Prepared request is not the fixed-worker intervention")
        if planned["worker_payload_hashes"] != [
            digest(a.payload) for a in source.request(planned["qid"]).context.artifacts
        ]:
            raise ValueError("Prepared worker payload hash mismatch")
