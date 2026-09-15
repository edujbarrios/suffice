from suffice.comparison import compare_results
from suffice.config import OptimizationConfig
from suffice.evaluators import (
    ContainsEvaluator,
    ExactMatchEvaluator,
    NumericEvaluator,
    StructuredEvaluator,
)
from suffice.models import AgentRunResult, ExperimentResult
from suffice.tokens import CountSource, TokenCategory, TokenCount, TokenTrace


def case(success: bool, tokens: int) -> AgentRunResult:
    trace = TokenTrace({TokenCategory.USER: TokenCount(tokens, CountSource.PROVIDER_REPORTED)})
    return AgentRunResult("answer", success=success, token_trace=trace)


def test_deterministic_evaluators() -> None:
    assert ExactMatchEvaluator().evaluate(" Oslo ", "oslo")
    assert ContainsEvaluator().evaluate("The answer is Oslo.", "Oslo")
    assert StructuredEvaluator().evaluate('{"status":"shipped"}', {"status": "shipped"})
    assert NumericEvaluator().evaluate("42.0", 42)


def test_quality_loss_rejects_apparent_savings() -> None:
    baseline = ExperimentResult([case(True, 100), case(True, 100)])
    candidate = ExperimentResult([case(True, 40), case(False, 40)])
    comparison = compare_results(
        baseline,
        candidate,
        OptimizationConfig(minimum_success_rate=0.95, maximum_success_drop=0.01),
    )
    assert comparison.token_reduction_percentage == 0.6
    assert not comparison.accepted
    assert "quality" in comparison.reason


def test_failed_runs_are_not_tokens_per_successful_task() -> None:
    result = ExperimentResult([case(False, 1)])
    assert result.tokens_per_successful_task is None
