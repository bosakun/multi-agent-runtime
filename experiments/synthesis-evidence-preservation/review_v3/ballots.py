"""Validate human-supplied forms and reconcile anonymous IDs; no semantic filling."""

from review_v3.schema import STAGE_MODELS, Registry


def validate_ballot(phase, value, reviewer, codebook_version=None):
    if phase in ("R1", "R2"):
        registry = Registry.model_validate(value)
        if not registry.judgments:
            raise ValueError("Independent human registry provenance required")
        if any(
            j.reviewer_id != reviewer
            or j.registry_phase != phase
            or j.judgment_status != "independent"
            for j in registry.judgments
        ):
            raise ValueError("Registry ballot is not this reviewer's independent pass")
        if phase == "R1" and (
            any(f.reference_basis != "raw_discovery" for f in registry.facts)
            or any(p.path_basis != "raw_discovered_alternative" for p in registry.paths)
        ):
            raise ValueError("Gold anchoring cannot appear in raw-only R1")
        return registry.model_dump(mode="json")
    allowed = {"S5a", "S5b"} if phase == "S5" else {phase}
    if not isinstance(value, list) or not value:
        raise ValueError("Nonempty stage ballot list required")
    result, keys = [], set()
    for entry in value:
        if set(entry) != {"stage", "annotation"} or entry["stage"] not in allowed:
            raise ValueError("Unexpected stage or fields in independent ballot")
        annotation = STAGE_MODELS[entry["stage"]].model_validate(entry["annotation"])
        if annotation.reviewer_id != reviewer or annotation.codebook_version != codebook_version:
            raise ValueError("Reviewer/codebook mismatch")
        key = (
            entry["stage"],
            annotation.question_id,
            annotation.path_id,
            annotation.fact_id,
            annotation.worker_id,
            annotation.arm,
            annotation.route,
        )
        if key in keys:
            raise ValueError("Duplicate annotation unit")
        keys.add(key)
        result.append({"stage": entry["stage"], "annotation": annotation.model_dump(mode="json")})
    return result


def reconcile_stage_ids(ballot, private_linkage):
    """Creates separate normalized copy; anonymous independent ballot is preserved."""
    aliases = private_linkage["aliases"]
    workers = {
        alias: original
        for original, alias in aliases.items()
        if original not in ("question", "arm")
    }
    result = []
    for entry in ballot:
        annotation = dict(entry["annotation"])
        if annotation["question_id"] != aliases["question"]:
            raise ValueError("Anonymous case linkage mismatch")
        annotation["question_id"] = private_linkage["question_id"]
        if annotation.get("worker_id") is not None:
            if annotation["worker_id"] not in workers:
                raise ValueError("Anonymous Worker linkage mismatch")
            annotation["worker_id"] = workers[annotation["worker_id"]]
        if annotation.get("arm") is not None:
            if annotation["arm"] != aliases["arm"]:
                raise ValueError("Anonymous arm linkage mismatch")
            annotation["arm"] = private_linkage["arm"]
        result.append({"stage": entry["stage"], "annotation": annotation})
    return result


def reconcile_registry_ids(registry, private_linkage):
    """New pre-freeze coordinator projection; raw independent ballot stays intact."""
    if registry.frozen_hash:
        raise ValueError("Normalize IDs BEFORE freeze, never mutate primary frozen registry")
    value = registry.model_dump(mode="json")
    if value["question"]["question_id"] != private_linkage["aliases"]["question"]:
        raise ValueError("Anonymous registry linkage mismatch")
    value["question"]["question_id"] = private_linkage["question_id"]
    for member in value["memberships"]:
        member["question_id"] = private_linkage["question_id"]
    return Registry.model_validate(value)
