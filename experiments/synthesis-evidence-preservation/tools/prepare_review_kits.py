"""Prepare local public-only reviewer slots; never produce human judgments."""

import hashlib
import json
import sys
import uuid
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
sys.path[:0] = [
    str(STUDY / "src"),
    str(STUDY.parents[1]),
    str(STUDY.parents[1] / "experiments/epistemic-diversity"),
    str(STUDY.parents[1] / "experiments/epistemic-diversity/src"),
]
from synthesis_study.io import exclusive, file_hash, read  # noqa: E402
from synthesis_study.runner import now, verify_seal  # noqa: E402


def order(codes, slot):
    return sorted(
        codes,
        key=lambda code: hashlib.sha256(
            f"20260930:human-review:{slot}:{code}".encode()
        ).hexdigest(),
    )


def blank(case_code, kind, calibration=False):
    return {
        "case_code": case_code,
        "kind": kind,
        "calibration": calibration,
        "reviewer_id": None,
        "criteria_revision": None,
        "reviewed_at": None,
        "final_supported": None,
        "cause_labels": [],
        "rationale": None,
        "confidence": None,
        "facts": [],
        "fact_entry_fields": [
            "fact_id",
            "source_sentence_ids",
            "necessary_fact",
            "local_availability",
            "citation_supported",
            "worker_extraction",
            "published_output_locations",
            "synthesis_input_locations",
            "transfer",
            "synthesis",
            "cause_labels",
            "rationale",
            "confidence",
        ],
        "status": "not_reviewed",
    }


def prepare():
    verify_seal()
    source = read(STUDY / "reports/source-audit/audit.json")
    report = STUDY / "reports/real-fixed-workers-20260930"
    completion = read(report / "completion-audit.json")
    if not completion["passed_model_comparison"] or completion["provider"] != "real":
        raise ValueError("Human kits require the complete real comparison, not Mock")
    cases = {case["case_code"]: case for case in source["cases"]}
    calibration = [code for code, case in cases.items() if case["calibration"]]
    new_files = {p.stem: p for p in (report / "review/public").glob("*.json")}
    if len(cases) != 30 or len(calibration) != 2 or len(new_files) != 72:
        raise ValueError("Incomplete review corpus")
    inputs = {
        STUDY / "reports/source-audit/audit.json": file_hash(
            STUDY / "reports/source-audit/audit.json"
        ),
        report / "completion-audit.json": file_hash(report / "completion-audit.json"),
    }
    root = STUDY / "reports/review-kits" / ("prepared-" + uuid.uuid4().hex)
    manifests = []
    for slot in ["reviewer_1", "reviewer_2"]:
        destination = root / slot
        sequence = calibration + order([c for c in cases if c not in calibration], slot)
        sequence += order(list(new_files), slot)
        hashes = {}
        for code in sequence:
            is_source = code in cases
            packet = (
                STUDY / "reports/review/public-source" / (code + ".md")
                if is_source
                else new_files[code]
            )
            inputs[packet] = file_hash(packet)
            if not is_source:
                value = read(packet)
                if (
                    set(value)
                    != {"case_code", "question", "public_sentences", "synthesis_input", "output"}
                    or value["case_code"] != code
                ):
                    raise ValueError("Public packet contains unexpected fields")
            output = destination / "public" / packet.name
            exclusive(output, packet.read_text(encoding="utf-8"), text=True)
            hashes["public/" + output.name] = file_hash(output)
            form = blank(code, "source" if is_source else "final", code in calibration)
            if is_source:
                # The primary target is C3; the reference conditions remain anonymous.
                mapping = cases[code]["blind_reference_mapping"]
                form["target_reference"] = next(
                    label for label, condition in mapping.items() if condition == "C3"
                )
            output = destination / "forms" / (code + ".json")
            exclusive(output, form)
            hashes["forms/" + output.name] = file_hash(output)
        instruction = (
            "# 独立判定用のローカル資料\n\n"
            "担当者未定のslotです。人間による判定はまだありません。\n\n"
            "1. criteria.mdを読み、view-order.jsonの最初の2問で基準を校正します。\n"
            "2. 担当者IDと合意した基準revisionを記録します。残りは相談せず判定します。\n"
            "3. publicの原文・公開出力を読み、formsに必要な事実と根拠を記録します。"
            "sourceのtarget_referenceが主判定対象で、他のreferenceは参照用です。\n"
            "4. sourceは事実ごとにfactsへ追記します。局所情報、公開出力、合成入力の"
            "該当箇所を分けます。判断不能はunclear/undeterminedを明記します。\n"
            "5. finalの72件も全て判定します。最終内容の支持根拠をrationaleへ記録します。\n"
            "6. 独立判定を固定して返却し、その後に協議します。協議結果は別versionへ保存します。\n\n"
            "空欄と空のfactsは未実施です。AIによる記入は独立人手判定に数えません。"
            "本文の長さから条件を推測できるため完全なblindとは主張しません。"
            "このフォルダに正解、条件対応表、集計スコアは含めません。"
            "基準固定後に必要な評価資料があれば評価担当から別途受け取ります。\n"
        )
        exclusive(destination / "START-HERE.md", instruction, text=True)
        exclusive(
            destination / "criteria.md",
            (STUDY / "REVIEW.md").read_text(encoding="utf-8"),
            text=True,
        )
        exclusive(
            destination / "view-order.json",
            {
                "slot": slot,
                "assigned_reviewer": None,
                "case_codes": sequence,
                "calibration_first": calibration,
                "source_cases": 30,
                "final_cases": 72,
                "completed_human_reviews": 0,
            },
        )
        for filename in ["START-HERE.md", "criteria.md", "view-order.json"]:
            hashes[filename] = file_hash(destination / filename)
        exclusive(
            destination / "packet-manifest.json",
            {
                "slot": slot,
                "case_count": 102,
                "files": hashes,
                "gold_included": False,
                "condition_mapping_included": False,
                "aggregate_scores_included": False,
                "reviewer_assigned": False,
            },
        )
        manifests.append(
            {
                "slot": slot,
                "path": destination.relative_to(STUDY).as_posix(),
                "packet_manifest_sha256": file_hash(destination / "packet-manifest.json"),
            }
        )
    for path, expected in inputs.items():
        if file_hash(path) != expected:
            raise ValueError("Source packet changed during preparation")
    audit = {
        "created_at": now(),
        "prepared_slots": manifests,
        "source_files_preserved": len(inputs),
        "assigned_reviewers": 0,
        "completed_reviewers": 0,
        "full_research_completed": False,
        "status": "prepared_awaiting_two_independent_humans",
    }
    exclusive(root / "preparation-audit.json", audit)
    print(
        json.dumps(
            {
                "root": str(root),
                "case_count_per_slot": 102,
                "assigned_reviewers": 0,
                "completed_reviewers": 0,
            },
            indent=2,
        )
    )
    return root


if __name__ == "__main__":
    prepare()
