"""Validate immutable sources without loading private gold into replay inputs."""

from pathlib import Path
from typing import Any

from external_benchmarks.models import PublicQuestion, WorkerAnswer
from native_pilot.provider import native_body

from app.llm.provider import ModelRequest
from synthesis_study.io import REPO, STUDY, digest, file_hash, read


def citations(payload: dict[str, Any]) -> list[str]:
    result = []
    for finding in payload["findings"]:
        result.extend(finding["evidence_ids"])
    result.extend(payload["uncertainty"]["evidence_ids"])
    return list(dict.fromkeys(result))


class Sources:
    def __init__(self):
        self.spec = read(STUDY / "study.json")
        self.hashes: dict[str, str] = {}
        for reference in self.spec["source_files"]:
            path = REPO / reference["path"]
            self.track(path)
            if self.hashes[reference["path"]] != reference["sha256"]:
                raise ValueError("Source hash mismatch: " + reference["path"])
        cumulative = read(REPO / self.spec["source_files"][2]["path"])
        self.metadata = cumulative["metadata"]
        self.records = {(r["question_id"], r["condition"]): r for r in cumulative["records"]}
        self.ids = self.metadata["task_ids"]
        if (
            len(self.ids) != 30
            or len(set(self.ids)) != 30
            or len(self.records) != 150
            or sum(r["calls"] for r in self.records.values()) != 510
            or any(
                r["status"] != "succeeded" or r["errors"] or any(r["audit"].values())
                for r in self.records.values()
            )
            or self.spec["main_question_ids"] != self.ids[6:]
        ):
            raise ValueError("Source cohort differs from fixed completed experiment")
        self.questions = {}
        self.calls: dict[tuple[str, str], dict[str, Any]] = {}
        scorer = (
            REPO
            / "experiments/epistemic-diversity/external_benchmarks/vendor/hotpot_evaluate_v1.py"
        )
        self.track(scorer)
        if file_hash(scorer) != self.spec["evaluation"]["scorer_sha256"]:
            raise ValueError("Official evaluator drift")
        for qid in self.ids:
            # Hash private evaluation material without loading it into input generation.
            self.track(REPO / self.spec["private_evaluation_root"] / f"{qid}.json")
            path = REPO / self.spec["public_data_root"] / f"{qid}.json"
            self.track(path)
            question = PublicQuestion.model_validate(read(path))
            if question.id != qid:
                raise ValueError("Public question ID mismatch")
            self.questions[qid] = question
            for condition in ["C1", "C2", "C3"]:
                self.calls[qid, condition] = self.load_calls(qid, condition)
                self.validate_workers(qid, condition)

    def track(self, path: Path) -> None:
        relative = path.resolve().relative_to(REPO).as_posix()
        self.hashes[relative] = file_hash(path)

    def resolve(self, value: str) -> Path:
        path = Path(value)
        if not path.exists():
            normalized = value.replace("\\", "/")
            marker = "/experiments/epistemic-diversity/"
            if marker not in normalized:
                raise ValueError("Cannot resolve source root")
            path = REPO / "experiments/epistemic-diversity" / normalized.split(marker, 1)[1]
        path = path.resolve()
        path.relative_to(REPO)
        return path

    def load_calls(self, qid: str, condition: str) -> dict[str, Any]:
        root = self.resolve(self.metadata["journal_roots"][f"{qid}:{condition}"])
        result = {}
        for path in sorted(root.glob("*.json")):
            self.track(path)
            call = read(path)
            if call["agent_id"] in result or call["error"] or not call["response"]:
                raise ValueError("Ambiguous or unsuccessful source journal")
            result[call["agent_id"]] = call
        if set(result) != {"worker_0", "worker_1", "worker_2", "synthesizer"}:
            raise ValueError("Missing source agent")
        for agent, call in result.items():
            if call["run_id"] == self.records[qid, condition]["run_id"]:
                continue
            if (
                condition != "C1"
                or qid != self.metadata["failed_question"]
                or agent not in self.metadata["restored_workers"]
            ):
                raise ValueError("Source run ID mismatch")
            original_root = (
                REPO
                / "experiments/epistemic-diversity/runs"
                / "hotpotqa-protocol31-qwen3-14b-windows/additional/call-journal"
                / qid
                / condition
            )
            originals = [
                read(p) for p in original_root.glob("*.json") if read(p)["agent_id"] == agent
            ]
            if len(originals) != 1 or digest(originals[0]) != digest(call):
                raise ValueError("Restored worker no longer matches original failed campaign")
        return result

    def validate_workers(self, qid: str, condition: str) -> None:
        calls = self.calls[qid, condition]
        context = calls["synthesizer"]["request"]["context"]
        if (
            context["task"] != self.questions[qid].question
            or context["inputs"]
            or context["knowledge"]
        ):
            raise ValueError("Source synthesis context drift")
        artifacts = context["artifacts"]
        if [a["producer"] for a in artifacts] != self.spec["worker_order"]:
            raise ValueError("Source artifact order drift")
        for worker, artifact in zip(self.spec["worker_order"], artifacts, strict=True):
            call = calls[worker]
            payload = call["response"]["output"]
            validated = WorkerAnswer.model_validate(payload).model_dump(mode="json")
            if digest(validated) != digest(artifact["payload"]):
                raise ValueError(
                    "Worker publication differs from transmitted artifact: "
                    f"{qid} {condition} {worker}"
                )
            available = {item["id"] for item in call["request"]["context"]["knowledge"]}
            if not set(citations(payload)).issubset(available):
                raise ValueError("Source worker cites an inaccessible sentence")
        # Exercise existing typed scope/schema without executing any workflow.
        ModelRequest.model_validate(calls["synthesizer"]["request"])

    def request(self, qid: str) -> ModelRequest:
        return ModelRequest.model_validate(self.calls[qid, "C3"]["synthesizer"]["request"])

    def excerpt(self, qid: str) -> tuple[str, list[str]]:
        sentences = {sentence.id: sentence for sentence in self.questions[qid].sentences}
        ids = []
        for worker in self.spec["worker_order"]:
            ids.extend(citations(self.calls[qid, "C3"][worker]["response"]["output"]))
        ids = list(dict.fromkeys(ids))
        selected = [sentences[sid] for sid in ids]
        return "\n\n".join(
            f"[{s.id}] {s.title} ({s.sentence_index})\n{s.text}" for s in selected
        ), ids

    def verify_preservation(self) -> dict[str, Any]:
        changed = [
            relative
            for relative, expected in self.hashes.items()
            if file_hash(REPO / relative) != expected
        ]
        return {"passed": not changed, "checked_files": len(self.hashes), "changed": changed}

    def verify_tokenizer(self, tokenizer: Any) -> dict[str, Any]:
        observations = []
        for qid in self.ids:
            for agent, call in self.calls[qid, "C3"].items():
                body = native_body(ModelRequest.model_validate(call["request"]))
                predicted = tokenizer.prompt_count(body)
                measured = call["response"]["usage"]["input_tokens"]
                observations.append(
                    {
                        "qid": qid,
                        "agent": agent,
                        "predicted": predicted,
                        "measured": measured,
                        "difference": predicted - measured,
                    }
                )
        return {
            "calls": len(observations),
            "exact_matches": sum(row["difference"] == 0 for row in observations),
            "max_absolute_difference": max(abs(row["difference"]) for row in observations),
            "observations": observations,
        }
