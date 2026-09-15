from __future__ import annotations

import statistics
from dataclasses import dataclass

from suffice.models import ExperimentResult
from suffice.tokens import TokenCategory


@dataclass(frozen=True)
class Metrics:
    success_rate: float
    average_latency_ms: float
    average_tokens_per_task: float
    median_tokens_per_task: float
    tokens_per_successful_task: float | None
    input_tokens: int
    output_tokens: int
    tool_overhead: int
    context_overhead: int
    category_totals: dict[str, int]


@dataclass(frozen=True)
class FrontierPoint:
    budget: int
    success_rate: float
    observed_average_tokens: float


def calculate_metrics(result: ExperimentResult) -> Metrics:
    totals = [case.token_trace.total or 0 for case in result.cases]
    categories: dict[str, int] = {}
    for case in result.cases:
        for category, count in case.token_trace.counts.items():
            categories[category.value] = categories.get(category.value, 0) + (count.count or 0)
    output = categories.get(TokenCategory.ASSISTANT_OUTPUT.value, 0)
    tool_overhead = categories.get(TokenCategory.TOOLS.value, 0) + categories.get(
        TokenCategory.TOOL_OUTPUT.value, 0
    )
    context_overhead = sum(
        categories.get(category.value, 0)
        for category in (
            TokenCategory.HISTORY,
            TokenCategory.CONTEXT,
            TokenCategory.MEMORY,
            TokenCategory.RETRIEVAL,
        )
    )
    return Metrics(
        success_rate=result.success_rate,
        average_latency_ms=(
            statistics.fmean(case.latency_ms for case in result.cases) if result.cases else 0.0
        ),
        average_tokens_per_task=statistics.fmean(totals) if totals else 0.0,
        median_tokens_per_task=statistics.median(totals) if totals else 0.0,
        tokens_per_successful_task=result.tokens_per_successful_task,
        input_tokens=sum(totals) - output,
        output_tokens=output,
        tool_overhead=tool_overhead,
        context_overhead=context_overhead,
        category_totals=categories,
    )


def efficiency_frontier(sweep: dict[int, ExperimentResult]) -> list[FrontierPoint]:
    return [
        FrontierPoint(
            budget,
            result.success_rate,
            calculate_metrics(result).average_tokens_per_task,
        )
        for budget, result in sorted(sweep.items())
    ]


def minimum_successful_token_budget(
    sweep: dict[int, ExperimentResult], required_success_rate: float = 1.0
) -> int | None:
    qualifying = [
        budget for budget, result in sweep.items() if result.success_rate >= required_success_rate
    ]
    return min(qualifying) if qualifying else None
