from suffice.metrics import calculate_metrics, efficiency_frontier, minimum_successful_token_budget
from suffice.models import AgentRunResult, ExperimentResult
from suffice.tokens import CountSource, TokenCategory, TokenCount, TokenTrace


def result(successes: list[bool], tokens: int) -> ExperimentResult:
    return ExperimentResult(
        [
            AgentRunResult(
                "x",
                success=success,
                token_trace=TokenTrace(
                    {
                        TokenCategory.SYSTEM: TokenCount(tokens - 2, CountSource.ESTIMATED),
                        TokenCategory.ASSISTANT_OUTPUT: TokenCount(2, CountSource.ESTIMATED),
                    }
                ),
            )
            for success in successes
        ]
    )


def test_metrics_report_quality_beside_token_cost() -> None:
    metrics = calculate_metrics(result([True, False], 10))
    assert metrics.success_rate == 0.5
    assert metrics.average_latency_ms == 0
    assert metrics.average_tokens_per_task == 10
    assert metrics.tokens_per_successful_task == 10
    assert metrics.input_tokens == 16
    assert metrics.output_tokens == 4


def test_frontier_and_minimum_successful_budget() -> None:
    sweep = {512: result([False], 100), 1024: result([True], 200), 2048: result([True], 300)}
    assert [point.budget for point in efficiency_frontier(sweep)] == [512, 1024, 2048]
    assert minimum_successful_token_budget(sweep) == 1024
    assert minimum_successful_token_budget(sweep, 1.1) is None
