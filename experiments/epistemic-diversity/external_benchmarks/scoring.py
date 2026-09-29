"""Run pinned upstream scoring; only redirect its optional ujson import to stdlib JSON."""

import ast
import io
import json
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

from external_benchmarks.models import PrivateGold
from external_benchmarks.provenance import SCORER_SHA256, file_sha256

SCORER = Path(__file__).parent / "vendor/hotpot_evaluate_v1.py"


def upstream() -> dict[str, Any]:
    if file_sha256(SCORER) != SCORER_SHA256:
        raise ValueError("Official evaluator checksum mismatch")
    tree = ast.parse(SCORER.read_text(encoding="utf-8"))
    imports = [
        node
        for node in tree.body
        if isinstance(node, ast.Import)
        and [(a.name, a.asname) for a in node.names] == [("ujson", "json")]
    ]
    if len(imports) != 1:
        raise ValueError("Unexpected upstream JSON import")
    tree.body.remove(imports[0])
    namespace: dict[str, Any] = {"__name__": "pinned_hotpot_evaluator", "json": json}
    # Pinned Apache-2.0 code only; no input-derived code or edits to the vendor file.
    exec(compile(tree, str(SCORER), "exec"), namespace)
    return namespace


def score(predictions: dict[str, Any], gold: list[PrivateGold]) -> dict[str, float]:
    ids = {item.id for item in gold}
    if (
        not ids
        or set(predictions.get("answer", {})) != ids
        or set(predictions.get("sp", {})) != ids
    ):
        raise ValueError("Predictions must cover the exact nonempty selected cohort")
    rows = [
        {
            "_id": item.id,
            "answer": item.answer,
            "supporting_facts": [list(pair) for pair in item.supporting_facts],
        }
        for item in gold
    ]
    with tempfile.TemporaryDirectory(prefix="hotpot-official-") as temporary:
        prediction_file = Path(temporary) / "predictions.json"
        gold_file = Path(temporary) / "gold.json"
        prediction_file.write_text(json.dumps(predictions, ensure_ascii=False), encoding="utf-8")
        gold_file.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
        output = io.StringIO()
        with redirect_stdout(output):
            upstream()["eval"](str(prediction_file), str(gold_file))
    result = ast.literal_eval(output.getvalue().strip())
    if not isinstance(result, dict) or len(result) != 12:
        raise ValueError("Unexpected official metric output")
    return {key: float(value) for key, value in result.items()}
