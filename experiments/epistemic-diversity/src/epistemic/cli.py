"""Explicit plan/run/analyze stages; a dry plan never calls a model."""

import argparse
import asyncio
import json
import os
from pathlib import Path

from epistemic.analysis import analyze
from epistemic.benchmark import build_benchmark
from epistemic.benchmark_audit import write_audit
from epistemic.benchmark_v2 import SEED, VERSION, build_v2
from epistemic.figures import generate
from epistemic.freeze import FREEZE_PATH, bind_model, seal, verify
from epistemic.models import ModelSettings
from epistemic.paths import read_json
from epistemic.review import human_review
from epistemic.runner import execute_campaign, make_plan


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    benchmark = sub.add_parser("benchmark", help="Materialize a versioned public/gold dataset")
    benchmark.add_argument("--benchmark-version", choices=["1.0.0", VERSION], default=VERSION)
    sub.add_parser("audit", help="Run the static v2 quality audit")
    freezing = sub.add_parser(
        "freeze", help="Seal benchmark/protocol/source before model execution"
    )
    freezing.add_argument("--output", type=Path, default=FREEZE_PATH)
    check = sub.add_parser("verify-freeze")
    check.add_argument("--freeze", type=Path, default=FREEZE_PATH)
    binding = sub.add_parser("bind-model", help="Record model/endpoint selection before paid calls")
    binding.add_argument("--model", required=True)
    binding.add_argument(
        "--endpoint", default=os.getenv("MODEL_BASE_URL", "https://api.openai.com/v1/")
    )
    binding.add_argument("--output", required=True, type=Path)
    binding.add_argument("--freeze", type=Path, default=FREEZE_PATH)
    binding.add_argument(
        "--execution-profile", choices=["standard", "local_ollama"], default="standard"
    )
    binding.add_argument("--campaign", type=Path)
    for command in ("plan", "run"):
        action = sub.add_parser(command)
        action.add_argument("--phase", choices=["pilot", "main", "full"], default="pilot")
        action.add_argument("--repetitions", type=int, default=1)
        action.add_argument(
            "--max-model-calls", type=int, default=int(os.getenv("MAX_MODEL_CALLS", "60"))
        )
        action.add_argument("--benchmark-version", choices=["1.0.0", VERSION], default=VERSION)
        if command == "run":
            action.add_argument("--provider", choices=["mock", "real"], default="mock")
            action.add_argument("--model", default="public-rule-mock-v2")
            action.add_argument("--temperature", type=float, default=0)
            action.add_argument("--max-output-tokens", type=int, default=2048)
            action.add_argument("--timeout", type=float)
            action.add_argument(
                "--execution-profile", choices=["standard", "local_ollama"], default="standard"
            )
            action.add_argument("--seed", type=int, default=SEED)
            action.add_argument("--campaign", required=True, type=Path)
            action.add_argument("--binding", type=Path)
            action.add_argument("--freeze", type=Path, default=FREEZE_PATH)
    analysis = sub.add_parser("analyze")
    analysis.add_argument("input", type=Path)
    analysis.add_argument("--output", required=True, type=Path)
    figures = sub.add_parser("figures")
    figures.add_argument("input", type=Path)
    figures.add_argument("--output", required=True, type=Path)
    review = sub.add_parser("human-review")
    review.add_argument("input", type=Path)
    review.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == "benchmark":
            if args.benchmark_version == VERSION:
                build_v2()
            else:
                build_benchmark()
        elif args.command == "audit":
            report = write_audit()
            print(json.dumps({"passed": report["passed"], "errors": report["errors"]}))
            if not report["passed"]:
                parser.exit(1, "Benchmark audit failed\n")
        elif args.command == "freeze":
            print(seal(args.output)["freeze_sha256"])
        elif args.command == "verify-freeze":
            print(verify(args.freeze)["freeze_sha256"])
        elif args.command == "bind-model":
            print(
                bind_model(
                    args.output,
                    args.model,
                    args.endpoint,
                    args.freeze,
                    execution_profile=args.execution_profile,
                    campaign=args.campaign,
                )["binding_sha256"]
            )
        elif args.command == "plan":
            print(
                json.dumps(
                    make_plan(
                        args.phase, args.repetitions, args.max_model_calls, args.benchmark_version
                    ),
                    indent=2,
                )
            )
        elif args.command == "run":
            settings = ModelSettings(
                provider=args.provider,
                model=args.model,
                temperature=args.temperature,
                max_output_tokens=args.max_output_tokens,
                timeout_seconds=args.timeout
                if args.timeout is not None
                else (300 if args.execution_profile == "local_ollama" else 90),
                execution_profile=args.execution_profile,
            )
            result = asyncio.run(
                execute_campaign(
                    args.campaign,
                    args.phase,
                    args.repetitions,
                    settings,
                    args.seed,
                    args.max_model_calls,
                    args.benchmark_version,
                    args.binding,
                    args.freeze,
                )
            )
            print(result)
        elif args.command == "analyze":
            print(analyze(args.input, args.output))
        elif args.command == "human-review":
            human_review(read_json(args.input), args.output)
        else:
            generate(args.input, args.output)
    except (ValueError, FileNotFoundError) as exc:
        parser.exit(2, f"{exc}\n")
