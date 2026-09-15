from pathlib import Path

from suffice.config import ExperimentConfig, ModelConfig
from suffice.experiments import budget_sweep, context_ablations


def test_budget_sweep_is_sorted_and_reproducible(tmp_path: Path) -> None:
    tasks = tmp_path / "tasks.jsonl"
    tasks.write_text(
        '{"id":"x","input":"q","expected":"a","metadata":{"minimum_budget":64}}\n',
        encoding="utf-8",
    )
    config = ExperimentConfig(
        "sweep", tasks, model=ModelConfig(max_tokens=128), token_budgets=(128, 32, 64)
    )
    results = budget_sweep(config)
    assert list(results) == [32, 64, 128]
    assert [result.success_rate for result in results.values()] == [0.0, 1.0, 1.0]


def test_context_ablation_variants() -> None:
    config = ExperimentConfig("x", Path("tasks"), history_tail=4, retrieval_top_k=3)
    variants = context_ablations(config)
    assert variants["no_history"].history_tail == 0
    assert variants["no_retrieval"].retrieval_top_k == 0
    assert variants["compact_tools"].tool_description_mode == "compact"
