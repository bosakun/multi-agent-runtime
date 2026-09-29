"""Public HotpotQA sentences are separate from private answers/support annotations."""

from pydantic import Field

from app.core.models import Model, Uncertainty


class Sentence(Model):
    id: str
    document: int
    title: str
    sentence_index: int = Field(ge=0)
    text: str


class PublicQuestion(Model):
    id: str
    question: str
    sentences: list[Sentence]


class PrivateGold(Model):
    id: str
    answer: str
    supporting_facts: list[tuple[str, int]]


class EmptyInput(Model):
    pass


class Finding(Model):
    text: str
    evidence_ids: list[str]


class WorkerAnswer(Model):
    candidate_answer: str
    findings: list[Finding]
    uncertainty: Uncertainty


class FinalAnswer(Model):
    answer: str
    evidence_ids: list[str]
    uncertainty: Uncertainty
