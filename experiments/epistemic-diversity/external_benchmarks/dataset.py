"""Lossless public/gold projection; gold-blind public-length-limited sampling."""

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from app.core.models import AgentContext, Knowledge
from external_benchmarks.models import PrivateGold, PublicQuestion, Sentence

SEED = 20260928
QUESTIONS = 6
MAX_CONTEXT_CHARS = 12000


def public_question(row: dict[str, Any]) -> PublicQuestion:
    sentences = []
    titles: set[str] = set()
    if not isinstance(row["_id"], str) or not isinstance(row["question"], str):
        raise ValueError("Hotpot ID/question must be text")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", row["_id"]):
        raise ValueError("Unsafe question ID")
    if len(row["context"]) != 10:
        raise ValueError("Require original distractor ten-document context")
    for document, (title, text) in enumerate(row["context"]):
        if not isinstance(title, str) or title in titles or not isinstance(text, list):
            raise ValueError("Require distinct original document titles")
        titles.add(title)
        for index, sentence in enumerate(text):
            if not isinstance(sentence, str):
                raise ValueError("Original sentence must be text")
            eid = (
                "hp_" + hashlib.sha256(f"{row['_id']}:{document}:{index}".encode()).hexdigest()[:16]
            )
            sentences.append(
                Sentence(
                    id=eid,
                    document=document,
                    title=title,
                    sentence_index=index,
                    text=sentence,
                )
            )
    return PublicQuestion(id=row["_id"], question=row["question"], sentences=sentences)


def private_gold(row: dict[str, Any], public: PublicQuestion) -> PrivateGold:
    gold = PrivateGold(
        id=row["_id"], answer=row["answer"], supporting_facts=row["supporting_facts"]
    )
    existing = {(s.title, s.sentence_index) for s in public.sentences}
    if gold.id != public.id:
        raise ValueError("Public/gold ID mismatch")
    if not set(gold.supporting_facts).issubset(existing):
        raise ValueError("Official support annotation absent from original context")
    return gold


def knowledge(question: PublicQuestion) -> dict[str, Knowledge]:
    return {
        s.id: Knowledge(
            id=s.id,
            content=json.dumps(
                {
                    "title": s.title,
                    "sentence_index": s.sentence_index,
                    "text": s.text,
                },
                ensure_ascii=False,
            ),
        )
        for s in question.sentences
    }


def public_context_chars(question: PublicQuestion) -> int:
    return len(
        AgentContext(
            agent_id="synthesizer",
            run_id="0" * 32,
            task=question.question,
            knowledge=list(knowledge(question).values()),
        ).model_dump_json()
    )


def select(
    rows: list[dict[str, Any]], count: int = QUESTIONS
) -> tuple[list[PublicQuestion], dict[str, int]]:
    eligible = []
    rejected = {"public_structure": 0, "public_length": 0}
    seen: set[str] = set()
    for row in rows:
        if row["_id"] in seen:
            raise ValueError("Duplicate official QA ID")
        seen.add(row["_id"])
        try:
            question = public_question(row)
        except (ValueError, TypeError, KeyError):
            rejected["public_structure"] += 1
            continue
        if public_context_chars(question) > MAX_CONTEXT_CHARS:
            rejected["public_length"] += 1
        else:
            eligible.append(question)
    eligible.sort(key=lambda q: hashlib.sha256(f"{SEED}:{q.id}".encode()).hexdigest())
    if count < 1 or len(eligible) < count:
        raise ValueError("Insufficient publicly eligible questions")
    return eligible[:count], {**rejected, "eligible": len(eligible), "total": len(rows)}


def supporting_pairs(question: PublicQuestion, evidence_ids: list[str]) -> list[list[str | int]]:
    mapping: dict[str, list[str | int]] = {
        s.id: [s.title, s.sentence_index] for s in question.sentences
    }
    if not set(evidence_ids).issubset(mapping):
        raise ValueError("Unknown public sentence citation")
    return [mapping[eid] for eid in evidence_ids]


def load_public(bundle: Path, ids: list[str]) -> list[PublicQuestion]:
    return [
        PublicQuestion.model_validate_json(
            (bundle / "public" / f"{qid}.json").read_text(encoding="utf-8"),
        )
        for qid in ids
    ]
