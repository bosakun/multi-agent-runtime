"""Offline preparation, bounded replay and independent post-generation analysis."""

import argparse
import json
from pathlib import Path

from synthesis_study.io import STUDY


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=[
            "prepare",
            "audit",
            "mock",
            "validate",
            "freeze",
            "bind",
            "verify",
            "run",
            "analyze",
        ],
    )
    parser.add_argument("--model-root", type=Path, default=Path.home() / ".ollama/models")
    parser.add_argument("--campaign", type=Path)
    parser.add_argument("--approve-real", action="store_true")
    args = parser.parse_args()
    if args.command == "prepare":
        from synthesis_study.prepare import make_inputs, save_inputs
        from synthesis_study.source import Sources
        from synthesis_study.tokenizer import LocalTokenizer

        value = make_inputs(Sources(), LocalTokenizer(args.model_root), enforce_limits=False)
        save_inputs(value)
        result = {
            "planned_calls": len(value["calls"]),
            "maximum_prompt_tokens": value["maximum_prompt_tokens"],
            "tokenizer_matches": value["tokenizer_verification"]["exact_matches"],
            "input_gate": not value["failures"],
        }
    elif args.command == "audit":
        from synthesis_study.audit import audit_sources
        from synthesis_study.source import Sources

        value = audit_sources(Sources())
        result = {
            key: value[key]
            for key in [
                "questions",
                "source_C3_agent_journals",
                "transfer_mismatches_after_schema_validation",
                "semantic_review_status",
            ]
        }
    elif args.command in {"mock", "run"}:
        from synthesis_study.runner import replay

        if args.command == "run" and not args.approve_real:
            parser.error("run requires --approve-real for the sealed 81-call budget")
        result = {"campaign": str(replay(mock=args.command == "mock", campaign=args.campaign))}
    elif args.command == "validate":
        from synthesis_study.validation import validate_offline

        result = validate_offline()
    elif args.command == "freeze":
        from synthesis_study.runner import freeze

        if not args.campaign:
            parser.error("freeze requires the completed --campaign Mock")
        value = freeze(args.campaign.resolve())
        result = {"freeze": str(STUDY / "freezes/v1.json"), "call_limit": value["call_limit"]}
    elif args.command == "bind":
        from synthesis_study.runner import bind

        value = bind()
        result = {
            "backend_version": value["backend"]["version"],
            "model": value["backend"]["model"]["name"],
            "gpu": value["host"]["gpu"],
        }
    elif args.command == "verify":
        from synthesis_study.runner import verify_seal

        result = {"verified": True, "call_limit": verify_seal()["call_limit"]}
    else:
        from synthesis_study.analysis import analyze

        if not args.campaign:
            parser.error("analyze requires --campaign")
        result = analyze(args.campaign.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
