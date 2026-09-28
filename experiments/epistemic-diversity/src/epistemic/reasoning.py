"""Public-rule proof utilities. No annotation loading or condition-dependent behavior."""

import itertools
import re

from app.core.models import Knowledge
from epistemic.models import Claim, InferenceRule, Pair

Proofs = dict[str, set[frozenset[str]]]


def pair(text: str) -> Pair:
    subject, value = text.strip().split("=", 1)
    return Pair(subject=subject.strip(), value=value.strip())


def observation(document: Knowledge) -> Claim | None:
    match = re.search(r"Observation: ([\w_]+) = ([\w_]+)\.", document.content)
    return Claim(subject=match[1], value=match[2], evidence_ids=[document.id]) if match else None


def insert(proofs: Proofs, key: str, support: frozenset[str]) -> bool:
    current = proofs.setdefault(key, set())
    if any(old <= support for old in current):
        return False
    current.difference_update({old for old in current if support < old})
    current.add(support)
    return True


def derive(claims: list[Claim], rules: list[InferenceRule]) -> Proofs:
    """Keep all minimal public evidence proofs, including alternative corroboration."""
    proofs: Proofs = {}
    for claim in claims:
        insert(proofs, claim.key(), frozenset(claim.evidence_ids))
    for _ in range(len(rules) + 2):
        changed = False
        for rule in rules:
            if all(p.key() in proofs for p in rule.premises):
                options = [list(proofs[p.key()]) for p in rule.premises]
                for support in itertools.product(*options):
                    changed |= insert(proofs, rule.conclusion.key(), frozenset().union(*support))
        if not changed:
            return proofs
    raise ValueError("Public rules did not converge; inspect cyclic benchmark")


def proof_order(support: frozenset[str]) -> tuple[int, list[str]]:
    return len(support), sorted(support)


def smallest_support(supports: set[frozenset[str]]) -> frozenset[str]:
    return min(supports, key=proof_order)


def supported_claims(proofs: Proofs) -> list[Claim]:
    return [
        Claim(
            **pair(key).model_dump(),
            evidence_ids=sorted(smallest_support(supports)),
        )
        for key, supports in sorted(proofs.items())
    ]
