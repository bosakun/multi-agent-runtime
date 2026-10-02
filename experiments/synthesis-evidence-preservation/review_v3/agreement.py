"""Pre-adjudication nominal agreement. No semantic adjudication is performed."""

from collections import Counter
from statistics import mean


def nominal(left, right):
    if len(left) != len(right):
        raise ValueError("Matched independent units required")
    pairs = [(a, b) for a, b in zip(left, right, strict=True) if a is not None and b is not None]
    n = len(pairs)
    a_counts = Counter(a for a, _ in pairs)
    b_counts = Counter(b for _, b in pairs)
    categories = sorted(set(a_counts) | set(b_counts))
    matrix = {
        a: {b: sum(x == a and y == b for x, y in pairs) for b in categories} for a in categories
    }
    observed = sum(a == b for a, b in pairs) / n if n else None
    expected = sum(a_counts[c] * b_counts[c] for c in categories) / (n * n) if n else None
    kappa = (observed - expected) / (1 - expected) if n and expected != 1 else None
    return {
        "n_evaluable": n,
        "potential_units": len(left),
        "missing_pair_n": len(left) - n,
        "raw_percent_agreement": observed * 100 if observed is not None else None,
        "cohens_kappa_unweighted": kappa,
        "undefined_reason": "no_evaluable_units" if not n else "Pe=1" if expected == 1 else None,
        "marginal_counts": {"reviewer1": dict(a_counts), "reviewer2": dict(b_counts)},
        "confusion_matrix": matrix,
    }


def stage_agreement(left, right, origin="independent"):
    if origin != "independent":
        raise ValueError("IAA requires pre-adjudication independent labels")
    if len(left) != len(right):
        raise ValueError("Matched units required")
    for a, b in zip(left, right, strict=True):
        fields = (
            "question_id",
            "path_id",
            "fact_id",
            "worker_id",
            "arm",
            "route",
            "codebook_version",
        )
        if type(a) is not type(b) or any(getattr(a, f) != getattr(b, f) for f in fields):
            raise ValueError("Unmatched unit/stage/codebook")
        if not a.reviewer_id or not b.reviewer_id or a.reviewer_id == b.reviewer_id:
            raise ValueError("Two distinct independent reviewer IDs required")
    applicable = [
        (a, b)
        for a, b in zip(left, right, strict=True)
        if a.applicability == b.applicability == "applicable"
    ]
    return {
        "applicability": nominal([s.applicability for s in left], [s.applicability for s in right]),
        "semantic": nominal([a.state for a, _ in applicable], [b.state for _, b in applicable]),
        "semantic_potential_units": len(left),
        "both_applicable_n": len(applicable),
        "applicability_excluded_n": len(left) - len(applicable),
    }


def multilabel(left, right, origin="independent"):
    if origin != "independent" or len(left) != len(right):
        raise ValueError("Matched pre-adjudication derived event sets required")
    pairs = [
        (set(a), set(b))
        for a, b in zip(left, right, strict=True)
        if a is not None and b is not None
    ]
    labels = sorted({label for a, b in pairs for label in a | b})
    jaccard = [len(a & b) / len(a | b) if a | b else 1.0 for a, b in pairs]
    nonempty = [value for value, (a, b) in zip(jaccard, pairs, strict=True) if a | b]
    return {
        "n_evaluable": len(pairs),
        "missing_pair_n": len(left) - len(pairs),
        "exact_set_agreement": mean(a == b for a, b in pairs) if pairs else None,
        "jaccard": mean(jaccard) if jaccard else None,
        "nonempty_union_n": len(nonempty),
        "nonempty_jaccard": mean(nonempty) if nonempty else None,
        "label_wise": {
            label: {
                **nominal([str(label in a) for a, _ in pairs], [str(label in b) for _, b in pairs]),
                "positive_counts": {
                    "reviewer1": sum(label in a for a, _ in pairs),
                    "reviewer2": sum(label in b for _, b in pairs),
                },
            }
            for label in labels
        },
    }


def scoped_stage_agreement(left, right, scope):
    """Primary IAA includes only explicitly human-approved independent case IDs."""
    if len(left) != len(right):
        raise ValueError("Matched independent units required")
    selected = [
        (a, b)
        for a, b in zip(left, right, strict=True)
        if a.question_id in scope.iaa_eligible_case_ids
    ]
    result = stage_agreement([a for a, _ in selected], [b for _, b in selected])
    result["scope_excluded_n"] = len(left) - len(selected)
    return result
