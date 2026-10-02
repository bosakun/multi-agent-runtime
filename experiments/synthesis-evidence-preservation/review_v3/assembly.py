"""Mechanical grouping only. Missing ballots stay missing; no votes are synthesized."""

from review_v3.schema import (
    S0,
    S1,
    S2,
    S3,
    STAGE_MODELS,
    ArmLabels,
    QuestionLabels,
    SharedLineage,
)


def assemble_question(registry, worker_ids, arm_ids, observations, label_origin):
    """Observations must be separately normalized copies, never overwritten raw ballots."""
    qid = registry.question.question_id
    facts = {f.fact_id for f in registry.facts}
    indexed = {}
    for entry in observations:
        stage = entry["stage"]
        label = STAGE_MODELS[stage].model_validate(entry["annotation"])
        if label.question_id != qid or label.fact_id is not None and label.fact_id not in facts:
            raise ValueError("Registry/label linkage mismatch")
        key = (stage, label.fact_id, label.worker_id, label.arm, label.path_id)
        if key in indexed:
            raise ValueError("Duplicate normalized observation")
        indexed[key] = label
    shared = []
    consumed = set()

    def take(stage, fact, worker=None, arm=None, path=None):
        key = (stage, fact, worker, arm, path)
        consumed.add(key)
        return indexed.get(key)

    for fact in sorted(facts):
        # S0 is one human reference judgment per fact, shared across Workers/arms.
        s0 = take("S0", fact) or S0(question_id=qid, fact_id=fact)
        for worker in worker_ids:
            common = dict(question_id=qid, fact_id=fact, worker_id=worker)
            shared.append(
                SharedLineage(
                    fact_id=fact,
                    worker_id=worker,
                    s0=s0,
                    s1=take("S1", fact, worker) or S1(**common),
                    s2=take("S2", fact, worker) or S2(**common),
                    s3=take("S3", fact, worker) or S3(**common),
                )
            )
    arms = {}
    for arm in arm_ids:
        s4 = {}
        for fact in sorted(facts):
            for worker in worker_ids:
                item = take("S4", fact, worker, arm)
                if item:
                    s4[f"{fact}|{worker}"] = item
        s5a = {fact: item for fact in sorted(facts) if (item := take("S5a", fact, arm=arm))}
        s5b = {
            p.path_id: item
            for p in registry.paths
            if (item := take("S5b", None, arm=arm, path=p.path_id))
        }
        arms[arm] = ArmLabels(s4=s4, s5a=s5a, s5b=s5b)
    if set(indexed) - consumed:
        raise ValueError("Unexpected Worker/arm/path or duplicated shared stage per arm")
    return QuestionLabels(registry=registry, shared=shared, arms=arms, label_origin=label_origin)
