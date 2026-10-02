"""Mechanical gates, not human assignment or automatic methodological sign-off."""

from typing import Literal

from pydantic import Field, model_validator

from review_v3.schema import Record, Registry
from review_v3.storage import digest, now

REGISTRY_ORDER = ["R1_OPEN", "R1_LOCKED", "R2_OPEN", "R2_LOCKED", "ADJUDICATION", "REGISTRY_FROZEN"]
STAGES = ["S1", "S2", "S3", "S4", "S5"]


class Lock(Record):
    reviewer_id: str
    phase: str
    content_hash: str
    timestamp: str
    version: str


class Workflow(Record):
    state: Literal[
        "R1_OPEN", "R1_LOCKED", "R2_OPEN", "R2_LOCKED", "ADJUDICATION", "REGISTRY_FROZEN"
    ] = "R1_OPEN"
    reviewer_ids: tuple[str, str]
    locks: list[Lock] = Field(default_factory=list)
    registry_hash: str | None = None
    codebook_version: str | None = None
    codebook_hash: str | None = None
    calibration_completed: bool = False
    human_signoff: str | None = None
    registry_frozen_at: str | None = None
    codebook_human_signoff: str | None = None
    codebook_frozen_at: str | None = None
    synthetic: bool = False

    @model_validator(mode="after")
    def ordered_history(self):
        if self.reviewer_ids[0] == self.reviewer_ids[1] or not all(self.reviewer_ids):
            raise ValueError("Two distinct explicitly supplied reviewer identities required")
        seen = set()
        for lock in self.locks:
            key = (lock.reviewer_id, lock.phase)
            if key in seen or lock.reviewer_id not in self.reviewer_ids:
                raise ValueError("Duplicate/unauthorized independent lock")
            if lock.phase not in ("R1", "R2", *STAGES):
                raise ValueError("Unknown lock phase")
            if lock.phase == "R2" and not {(r, "R1") for r in self.reviewer_ids} <= seen:
                raise ValueError("R2 before both R1 locks")
            if lock.phase in STAGES:
                prerequisites = {(lock.reviewer_id, p) for p in STAGES[: STAGES.index(lock.phase)]}
                if not prerequisites <= seen:
                    raise ValueError("Progressive lock history out of order")
            seen.add(key)
        position = REGISTRY_ORDER.index(self.state)
        for phase, threshold in (("R1", 1), ("R2", 3)):
            if position >= threshold and not {(r, phase) for r in self.reviewer_ids} <= seen:
                raise ValueError("Registry state lacks required independent locks")
        if self.state == "REGISTRY_FROZEN" and not (self.registry_hash and self.human_signoff):
            raise ValueError("Frozen registry needs explicit human sign-off/hash")
        return self

    def lock(self, reviewer, phase, value, version):
        if reviewer not in self.reviewer_ids or self.reviewer_ids[0] == self.reviewer_ids[1]:
            raise ValueError("Two distinct authorized human identities required")
        if any(item.reviewer_id == reviewer and item.phase == phase for item in self.locks):
            raise ValueError("Independent lock is immutable; use amendment/new workflow")
        if phase in ("R1", "R2"):
            if self.state != phase + "_OPEN":
                raise ValueError("Registry phase order violation")
        else:
            self.authorize(phase, reviewer)
        lock = Lock(
            reviewer_id=reviewer,
            phase=phase,
            content_hash=digest(value),
            timestamp=now(),
            version=version,
        )
        return self.model_copy(update={"locks": [*self.locks, lock]})

    def advance(self, target, registry: Registry | None = None, signoff=None):
        if self.state not in REGISTRY_ORDER or target not in REGISTRY_ORDER:
            raise ValueError("Unknown registry state")
        if REGISTRY_ORDER.index(target) != REGISTRY_ORDER.index(self.state) + 1:
            raise ValueError("Cannot skip/backtrack registry phases")
        if target in ("R1_LOCKED", "R2_LOCKED"):
            phase = target.split("_")[0]
            locked = {item.reviewer_id for item in self.locks if item.phase == phase}
            if locked != set(self.reviewer_ids) or len(locked) != 2:
                raise ValueError("Both independent ballots must be locked")
        updates = {"state": target}
        if target == "REGISTRY_FROZEN":
            if registry is None or not signoff or not registry.judgments:
                raise ValueError("Adjudicated registry and explicit human sign-off required")
            if any(j.judgment_status != "adjudicated" for j in registry.judgments):
                raise ValueError("Primary final registry must retain adjudicated provenance")
            if not registry.paths or any(p.validity is None for p in registry.paths):
                raise ValueError("Cannot freeze a blank registry")
            if any(s.support_set_sufficient is None for s in registry.support_sets):
                raise ValueError("Support-set judgments missing")
            if any(m.required_within_path is None for m in registry.memberships):
                raise ValueError("Path-conditional requiredness missing")
            if any(
                p.validity == "yes"
                and not any(
                    m.path_id == p.path_id and m.required_within_path == "yes"
                    for m in registry.memberships
                )
                for p in registry.paths
            ):
                raise ValueError("Valid path requires at least one required fact")
            updates.update(
                registry_hash=registry_digest(registry),
                human_signoff=signoff,
                registry_frozen_at=now(),
            )
        return self.model_copy(update=updates)

    def authorize(self, phase, reviewer):
        if reviewer not in self.reviewer_ids:
            raise ValueError("Unauthorized reviewer")
        if any(item.reviewer_id == reviewer and item.phase == phase for item in self.locks):
            raise ValueError("Phase already locked; preserve existing packet or use amendment")
        if phase == "R1":
            if self.state != "R1_OPEN":
                raise ValueError("R1 closed")
            return
        if phase == "R2":
            if self.state != "R2_OPEN":
                raise ValueError("Gold unavailable before both R1 locks")
            return
        if phase not in STAGES or self.state != "REGISTRY_FROZEN":
            raise ValueError("System outputs unavailable before registry freeze")
        if not (self.codebook_hash and self.codebook_version and self.calibration_completed):
            raise ValueError("Stage calibration and human-frozen codebook required")
        required = STAGES[: STAGES.index(phase)]
        completed = {item.phase for item in self.locks if item.reviewer_id == reviewer}
        if not set(required) <= completed:
            raise ValueError("Progressive disclosure requires own preceding locks")

    def freeze_codebook(self, version, codebook, calibration_completed, signoff):
        if self.codebook_hash or not calibration_completed or not signoff:
            raise ValueError("Explicit calibration/sign-off; no silent codebook mutation")
        return self.model_copy(
            update={
                "codebook_version": version,
                "codebook_hash": digest(codebook),
                "calibration_completed": True,
                "codebook_human_signoff": signoff,
                "codebook_frozen_at": now(),
            }
        )

    def verify_registry(self, registry):
        if not self.registry_hash or registry_digest(registry) != self.registry_hash:
            raise ValueError("Registry changed after freeze")


def registry_digest(registry):
    return digest(registry.model_dump(mode="json", exclude={"frozen_hash"}))


def frozen_registry(registry, workflow):
    workflow.verify_registry(registry)
    return Registry.model_validate(
        {**registry.model_dump(mode="json"), "frozen_hash": workflow.registry_hash}
    )
