"""Run demos and inspect durable traces without external model credentials."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from pydantic import JsonValue, ValidationError

from app.core.errors import RuntimeFault
from app.core.models import Status, WorkflowInput
from app.observability.flow import inspect_run, mermaid
from app.service import RuntimeService, Settings


def progress(kind: str, node: str | None, data: dict[str, JsonValue]) -> None:
    if kind == "AGENT_STARTED":
        print(f"[START] {node} attempt={data['attempt']}", file=sys.stderr)
    elif kind in {"AGENT_COMPLETED", "AGENT_FAILED"}:
        tag = "DONE" if kind == "AGENT_COMPLETED" else "FAIL"
        print(f"[{tag}] {node} {data['latency_ms']}ms", file=sys.stderr)
    elif kind in {"RETRY_SCHEDULED", "HUMAN_APPROVAL_REQUIRED"}:
        print(f"[{kind}] {node}", file=sys.stderr)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Isolated Multi-Agent Runtime")
    sub = root.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--workflow", choices=["investigation", "software_review"], required=True)
    run.add_argument("--input", type=Path, required=True)
    run.add_argument("--mode", choices=["isolated", "shared", "single"], default="isolated")
    run.add_argument("--approval", action="store_true")
    inspect = sub.add_parser("inspect")
    inspect.add_argument("run_id")
    inspect.add_argument("--mermaid", action="store_true")
    inspect.add_argument(
        "--content", action="store_true", help="Include potentially sensitive artifact payloads"
    )
    inspect.add_argument("--revision", type=int)
    resume = sub.add_parser("resume")
    resume.add_argument("run_id")
    resume.add_argument("--approve", metavar="NODE")
    resume.add_argument("--reject", metavar="NODE")
    cancel = sub.add_parser("cancel")
    cancel.add_argument("run_id")
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("--workflow", choices=["investigation", "software_review"], required=True)
    evaluate.add_argument("--input", type=Path, required=True)
    evaluate.add_argument("--case", type=Path, required=True)
    return root


async def execute(args: argparse.Namespace) -> int:
    if args.command == "evaluate":
        from app.evaluation.runner import compare

        print(json.dumps(await compare(args.workflow, args.input, args.case), indent=2))
        return 0
    runtime = RuntimeService(Settings.from_env(), observer=progress)
    await runtime.initialize()
    try:
        if args.command == "run":
            task = WorkflowInput.model_validate_json(args.input.read_text())
            run_id = await runtime.create_run(
                args.workflow, task, args.mode, approval=args.approval
            )
            run = await runtime.orchestrator.execute(run_id)
        elif args.command == "resume":
            if args.approve and args.reject:
                raise ValueError("Choose approve or reject")
            if args.approve or args.reject:
                await runtime.orchestrator.approve(
                    args.run_id, args.approve or args.reject, bool(args.approve)
                )
            run = await runtime.orchestrator.execute(args.run_id)
        elif args.command == "cancel":
            run = await runtime.orchestrator.cancel(args.run_id)
        else:
            run = (
                await runtime.repository.replay(args.run_id, args.revision)
                if args.revision
                else await runtime.repository.get(args.run_id)
            )
            print(mermaid(run) if args.mermaid else inspect_run(run, content=args.content))
            if not args.mermaid:
                for event in await runtime.repository.events(run.id):
                    if event.sequence <= run.event_count:
                        print(
                            f"  {event.sequence:04} {event.kind} {event.node_id or ''} {event.data}"
                        )
            return 0
        print(
            json.dumps(
                {"run_id": run.id, "status": run.status, "usage": run.usage().model_dump()},
                indent=2,
            )
        )
        return 1 if run.status in {Status.FAILED, Status.PARTIAL} else 0
    finally:
        await runtime.close()


def main() -> None:
    try:
        code = asyncio.run(execute(parser().parse_args()))
    except (RuntimeFault, KeyError, ValidationError, ValueError, OSError) as exc:
        # No raw validation payloads or environment values in terminal errors.
        print(
            f"Error: {exc.code if isinstance(exc, RuntimeFault) else type(exc).__name__}",
            file=sys.stderr,
        )
        code = 1
    raise SystemExit(code)
