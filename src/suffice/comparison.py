from __future__ import annotations

from dataclasses import dataclass

from suffice.config import OptimizationConfig
from suffice.models import ExperimentResult


@dataclass(frozen=True)
class Comparison:
    baseline_success_rate: float
    candidate_success_rate: float
    baseline_tokens: float
    candidate_tokens: float
    token_reduction: float
    token_reduction_percentage: float | None
    accepted: bool
    reason: str


def compare_results(
    baseline: ExperimentResult,
    candidate: ExperimentResult,
    constraint: OptimizationConfig,
) -> Comparison:
    baseline_tokens = _average_tokens(baseline)
    candidate_tokens = _average_tokens(candidate)
    reduction = baseline_tokens - candidate_tokens
    reduction_percentage = reduction / baseline_tokens if baseline_tokens else None
    success_drop = baseline.success_rate - candidate.success_rate
    quality_ok = (
        candidate.success_rate >= constraint.minimum_success_rate
        and success_drop <= constraint.maximum_success_drop
    )
    accepted = quality_ok and reduction > 0
    if not quality_ok:
        reason = "rejected: quality constraint not met"
    elif reduction <= 0:
        reason = "rejected: no token reduction"
    else:
        reason = "accepted: token reduction preserves required quality"
    return Comparison(
        baseline.success_rate,
        candidate.success_rate,
        baseline_tokens,
        candidate_tokens,
        reduction,
        reduction_percentage,
        accepted,
        reason,
    )


def _average_tokens(result: ExperimentResult) -> float:
    if not result.cases:
        return 0.0
    return sum(case.token_trace.total or 0 for case in result.cases) / len(result.cases)

