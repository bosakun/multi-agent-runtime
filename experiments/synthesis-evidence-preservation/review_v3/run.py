"""Explicit commands only; no automatic generation, annotation or real statistics."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from review_v3.ballots import validate_ballot  # noqa: E402
from review_v3.manifest import freeze_candidate  # noqa: E402
from review_v3.packets import PrivateSource, build_packet  # noqa: E402
from review_v3.schema import STAGE_MODELS, Registry, Scope  # noqa: E402
from review_v3.storage import ReviewStore, exclusive, read, verify_snapshot  # noqa: E402
from review_v3.workflow import Workflow, frozen_registry  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description="Empty v3 human review infrastructure")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("candidate")  # Print only; never marks final frozen.
    schema = commands.add_parser("schema")
    schema.add_argument("kind", choices=["registry", "scope", *STAGE_MODELS])
    validate = commands.add_parser("validate")
    validate.add_argument("kind", choices=["registry", "scope", *STAGE_MODELS])
    validate.add_argument("input")
    verify = commands.add_parser("verify-preservation")
    verify.add_argument("snapshot")
    verify.add_argument("--root", required=True)
    packet = commands.add_parser("packet")
    for name in ("source", "workflow", "registry", "phase", "reviewer", "destination", "scope"):
        packet.add_argument("--" + name, required=True)
    packet.add_argument("--arm")
    packet.add_argument("--case-alias")
    packet.add_argument("--arm-alias")
    packet.add_argument("--private-linkage", required=True)
    lock = commands.add_parser("lock")
    for name in ("workflow", "reviewer", "phase", "ballot", "version", "store", "unit"):
        lock.add_argument("--" + name, required=True)
    lock.add_argument("--output", required=True)
    advance = commands.add_parser("advance")
    advance.add_argument("--workflow", required=True)
    advance.add_argument("--target", required=True)
    advance.add_argument("--registry")
    advance.add_argument("--human-signoff")
    advance.add_argument("--output", required=True)
    advance.add_argument("--frozen-registry-output")
    codebook = commands.add_parser("freeze-codebook")
    for name in ("workflow", "codebook", "version", "human-signoff", "output"):
        codebook.add_argument("--" + name, required=True)
    codebook.add_argument("--calibration-completed", action="store_true", required=True)
    args = parser.parse_args(argv)
    models = {"registry": Registry, "scope": Scope, **STAGE_MODELS}
    if args.command == "candidate":
        result = freeze_candidate()
    elif args.command == "schema":
        result = models[args.kind].model_json_schema()
    elif args.command == "validate":
        models[args.kind].model_validate(read(args.input))
        result = {"mechanical_schema_valid": True, "semantic_review_performed": False}
    elif args.command == "verify-preservation":
        result = verify_snapshot(args.root, read(args.snapshot))
        if not result["passed"]:
            print(json.dumps(result))
            return 1
    elif args.command == "packet":
        linkage = Path(args.private_linkage).resolve()
        destination = Path(args.destination).resolve()
        if linkage.is_relative_to(destination) or linkage.exists():
            raise ValueError("Fresh private linkage must be outside reviewer export")
        registry = Registry.model_validate(read(args.registry))
        result = build_packet(
            PrivateSource.model_validate(read(args.source)),
            Workflow.model_validate(read(args.workflow)),
            registry,
            args.phase,
            args.reviewer,
            args.destination,
            args.arm,
            args.case_alias,
            args.arm_alias,
            Scope.model_validate(read(args.scope)),
        )
        # Linkage is NEVER inside reviewer export. Refuse its path within that folder.
        exclusive(linkage, result["private_linkage"])
        result = {"packet_manifest_hash": result["packet_manifest_hash"], "blank_form": True}
    elif args.command == "lock":
        workflow = Workflow.model_validate(read(args.workflow))
        ballot = validate_ballot(
            args.phase, read(args.ballot), args.reviewer, workflow.codebook_version
        )
        # These commands save user-supplied ballots; they never fill fields.
        updated = workflow.lock(args.reviewer, args.phase, ballot, args.version)
        slot = workflow.reviewer_ids.index(args.reviewer) + 1
        area = (
            f"registry_reviewer{slot}_raw"
            if args.phase in ("R1", "R2")
            else f"stage_labels_reviewer{slot}"
        )
        ReviewStore(args.store).append(area, args.unit, f"{args.phase}-{args.version}", ballot)
        exclusive(args.output, updated.model_dump(mode="json"))
        result = {"lock": updated.locks[-1].model_dump(), "immutable": True}
    elif args.command == "freeze-codebook":
        workflow = Workflow.model_validate(read(args.workflow))
        updated = workflow.freeze_codebook(
            args.version, read(args.codebook), args.calibration_completed, args.human_signoff
        )
        exclusive(args.output, updated.model_dump(mode="json"))
        result = {"codebook_hash": updated.codebook_hash, "human_signoff_recorded": True}
    else:
        workflow = Workflow.model_validate(read(args.workflow))
        registry = Registry.model_validate(read(args.registry)) if args.registry else None
        updated = workflow.advance(args.target, registry, args.human_signoff)
        if args.target == "REGISTRY_FROZEN":
            if not args.frozen_registry_output:
                raise ValueError("New immutable frozen registry destination required")
            exclusive(
                args.frozen_registry_output,
                frozen_registry(registry, updated).model_dump(mode="json"),
            )
        exclusive(args.output, updated.model_dump(mode="json"))
        result = {"registry_state": updated.state, "not_methodology_final_freeze": True}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
