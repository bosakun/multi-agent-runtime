"""Independent records survive; human resolution is a separate immutable version."""

from review_v3.schema import Adjudication


def save_adjudication(store, workflow, unit_id, version, records, final_labels):
    for reviewer in workflow.reviewer_ids:
        if not any(item.reviewer_id == reviewer and item.phase == "S5" for item in workflow.locks):
            raise ValueError("Both complete independent stage ballots must be locked first")
    validated = [Adjudication.model_validate(r) for r in records]
    if any(
        r.unit_id != unit_id or r.codebook_version != workflow.codebook_version for r in validated
    ):
        raise ValueError("Adjudication unit/codebook mismatch")
    store.append(
        "adjudication_log", unit_id, version, [r.model_dump(mode="json") for r in validated]
    )
    return store.append("final_adjudicated_labels", unit_id, version, final_labels)
