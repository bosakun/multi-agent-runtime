"""Question blocks stay intact. Configuration has no default seed/draws/CI policy."""

import math
import random
from typing import Literal

from pydantic import Field

from review_v3.schema import Record


class BootstrapConfig(Record):
    draws: int = Field(gt=0)
    seed: int
    ci_type: Literal["percentile"]
    confidence_level: float = Field(gt=0, lt=1)
    zero_denominator_rule: Literal["exclude_draw", "reject"]
    human_finalization: str | None = None


def resample_blocks(questions, config):
    if not questions:
        raise ValueError("No questions")
    ids = [q.registry.question.question_id for q in questions]
    if len(ids) != len(set(ids)):
        raise ValueError("Each source question must be unique")
    rng = random.Random(config.seed)
    for _ in range(config.draws):
        # Whole model including registry, Workers, shared records, and all arms.
        yield [
            questions[i].model_copy(deep=True)
            for i in rng.choices(range(len(questions)), k=len(questions))
        ]


def percentile(sorted_values, fraction):
    position = fraction * (len(sorted_values) - 1)
    low, high = math.floor(position), math.ceil(position)
    return sorted_values[low] + (sorted_values[high] - sorted_values[low]) * (position - low)


def clustered_bootstrap(questions, statistic, config):
    if any(q.label_origin == "independent" for q in questions):
        raise ValueError("Lineage bootstrap requires adjudicated labels or synthetic tests")
    if any(q.label_origin != "synthetic" for q in questions) and not config.human_finalization:
        raise ValueError("Real analysis requires human-finalized bootstrap configuration")
    values, excluded = [], 0
    for sample in resample_blocks(questions, config):
        value = statistic(sample)
        if value is None:
            if config.zero_denominator_rule == "reject":
                raise ValueError("Zero-denominator bootstrap draw")
            excluded += 1
        elif not math.isfinite(value):
            raise ValueError("Nonfinite statistic")
        else:
            values.append(value)
    values.sort()
    tail = (1 - config.confidence_level) / 2
    return {
        "config": config.model_dump(),
        "evaluable_draws": len(values),
        "excluded_draws": excluded,
        "interval": [percentile(values, tail), percentile(values, 1 - tail)] if values else None,
        "unit": "question-clustered; all arms and shared lineage retained",
    }


def macro_statistic(metric_name, sensitivity=False):
    # Aggregate rejects duplicate original question IDs; bootstrap repeats blocks
    # deliberately, so compute each within-question summary and average repeated draws.
    from statistics import mean

    from review_v3.metrics import metric_units, summarize

    def statistic(sample):
        rates = [
            summarize(
                metric_units(q, sensitivity).get(metric_name, []),
                metric_name == "publication_survival",
            )["rate"]
            for q in sample
        ]
        available = [r for r in rates if r is not None]
        return mean(available) if available else None

    return statistic
