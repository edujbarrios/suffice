from __future__ import annotations

from dataclasses import replace

from suffice.comparison import Comparison, compare_results
from suffice.config import ExperimentConfig
from suffice.experiment import Experiment
from suffice.models import ExperimentResult


def budget_sweep(config: ExperimentConfig) -> dict[int, ExperimentResult]:
    if not config.token_budgets:
        raise ValueError("token_budgets is required for a budget sweep")
    return {
        budget: Experiment(replace(config, model=replace(config.model, max_tokens=budget))).run()
        for budget in sorted(set(config.token_budgets))
    }


def compare_configs(baseline: ExperimentConfig, candidate: ExperimentConfig) -> Comparison:
    return compare_results(
        Experiment(baseline).run(),
        Experiment(candidate).run(),
        candidate.optimization,
    )


def context_ablations(config: ExperimentConfig) -> dict[str, ExperimentConfig]:
    """Return deterministic one-component-at-a-time experiment configurations."""
    variants = {"baseline": config}
    if config.history_tail is not None:
        variants["no_history"] = replace(config, history_tail=0)
    if config.retrieval_top_k is not None:
        variants["no_retrieval"] = replace(config, retrieval_top_k=0)
    variants["compact_tools"] = replace(config, tool_description_mode="compact")
    variants["compact_tool_outputs"] = replace(config, tool_output_mode="structured")
    return variants
