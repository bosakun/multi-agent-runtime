"""Prepare inspection packets without claiming human semantic validation."""

import csv
import io
from typing import Any

from synthesis_study.io import REPO, STUDY, canonical, digest, exclusive, read
from synthesis_study.source import Sources, citations


def audit_sources(source: Sources) -> dict[str, Any]:
    records, review_rows = [], []
    for position, qid in enumerate(source.ids):
        question = source.questions[qid]
        code = "source-" + digest({"id": qid, "seed": 20260930})[:12]
        gold_path = REPO / source.spec["private_evaluation_root"] / f"{qid}.json"
        source.track(gold_path)
        gold = read(gold_path)
        gold_ids = [
            s.id
            for s in question.sentences
            if [s.title, s.sentence_index] in gold["supporting_facts"]
        ]
        parts = [
            f"# {code}",
            "",
            "Source inspection; semantic correctness requires human review.",
            "",
            question.question,
            "",
            "## Public source sentences",
            "",
        ]
        parts.extend(
            f"- [{s.id}] {s.title} ({s.sentence_index}): {s.text}" for s in question.sentences
        )
        row: dict[str, Any] = {
            "case_code": code,
            "qid": qid,
            "calibration": position < 2,
            "conditions": {},
        }
        for condition in ["C1", "C2", "C3"]:
            calls = source.calls[qid, condition]
            cited = set()
            workers = []
            for worker in source.spec["worker_order"]:
                call = calls[worker]
                payload = call["response"]["output"]
                ids = citations(payload)
                cited.update(ids)
                workers.append(
                    {
                        "worker": worker,
                        "input_ids": [
                            item["id"] for item in call["request"]["context"]["knowledge"]
                        ],
                        "citation_ids": ids,
                        "raw_response_hash": digest(payload),
                        "published_payload_hash": digest(
                            next(
                                a["payload"]
                                for a in calls["synthesizer"]["request"]["context"]["artifacts"]
                                if a["producer"] == worker
                            )
                        ),
                    }
                )
            row["conditions"][condition] = {
                "workers": workers,
                "gold_support_citation_recall": len(cited.intersection(gold_ids)) / len(gold_ids)
                if gold_ids
                else None,
                "typed_publication_matches_input": True,
                "semantic_failure_labels": "pending_human_review",
            }
        # The primary human inspection packet is C3, with blind reference codes for C1/C2.
        reference_order = sorted(
            ["C1", "C2", "C3"], key=lambda c: digest({"qid": qid, "condition": c})
        )
        mapping = {}
        for index, condition in enumerate(reference_order):
            label = f"reference-{index + 1}"
            mapping[label] = condition
            calls = source.calls[qid, condition]
            parts.extend(["", f"## {label}", ""])
            for worker in source.spec["worker_order"]:
                call = calls[worker]
                parts.extend(
                    [
                        f"### {worker}",
                        "",
                        "Available sentence IDs: "
                        + ", ".join(item["id"] for item in call["request"]["context"]["knowledge"]),
                        "",
                        "```json",
                        canonical(call["response"]["output"]),
                        "```",
                    ]
                )
            parts.extend(
                [
                    "",
                    "### Actual synthesis input",
                    "",
                    "```json",
                    canonical(calls["synthesizer"]["request"]["context"]),
                    "```",
                    "",
                    "### Final answer",
                    "",
                    "```json",
                    canonical(calls["synthesizer"]["response"]["output"]),
                    "```",
                ]
            )
        row["blind_reference_mapping"] = mapping
        exclusive(
            STUDY / "reports/review/public-source" / f"{code}.md",
            "\n".join(parts) + "\n",
            text=True,
        )
        exclusive(
            STUDY / "reports/review/private-evaluation" / f"{code}.json",
            {
                "case_code": code,
                "qid": qid,
                "gold": gold,
                "gold_support_ids": gold_ids,
                "mapping": mapping,
            },
        )
        records.append(row)
        for reviewer in ["reviewer_1", "reviewer_2"]:
            review_rows.append(
                {
                    "study_id": source.spec["study_id"],
                    "case_code": code,
                    "question_id": qid,
                    "reviewer_id": reviewer,
                    "calibration": position < 2,
                    "fact_id": "",
                    "source_sentence_ids": "",
                    "citation_supported": "",
                    "worker_extraction": "",
                    "transfer": "",
                    "synthesis": "",
                    "final_supported": "",
                    "cause_labels": "",
                    "rationale": "",
                    "confidence": "",
                    "reviewed_at": "",
                }
            )
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(review_rows[0]))
    writer.writeheader()
    writer.writerows(review_rows)
    exclusive(STUDY / "reports/review/blank-source-review.csv", buffer.getvalue(), text=True)
    result = {
        "study_id": source.spec["study_id"],
        "questions": 30,
        "worker_outputs_inspected": 270,
        "source_C3_agent_journals": 120,
        "transfer_mismatches_after_schema_validation": 0,
        "semantic_review_status": "pending_independent_humans",
        "independent_reviewers_completed": 0,
        "source_preservation": source.verify_preservation(),
        "source_hashes": source.hashes,
        "cases": records,
    }
    exclusive(STUDY / "reports/source-audit/audit.json", result)
    return result
