from __future__ import annotations

from suffice.agents.base import AgentAdapter
from suffice.config import ExperimentConfig
from suffice.models import AgentRunResult, Task
from suffice.tokens import EstimatedTokenCounter, TokenCategory, TokenTrace


class MockAgentAdapter(AgentAdapter):
    """Offline adapter that deterministically returns each task's expected value."""

    def run(self, task: Task, config: ExperimentConfig) -> AgentRunResult:
        counter = EstimatedTokenCounter()
        trace = TokenTrace()
        trace.record(TokenCategory.SYSTEM, counter.count(config.system_prompt))
        trace.record(TokenCategory.USER, counter.count(task.input))
        required_tokens = int(task.metadata.get("minimum_budget", 0))
        succeeds_budget = config.model.max_tokens >= required_tokens
        output = task.expected if succeeds_budget else "[budget exhausted]"
        trace.record(TokenCategory.ASSISTANT_OUTPUT, counter.count(str(output)))
        return AgentRunResult(
            output=output,
            metadata={
                "input_tokens": trace.input_total,
                "output_tokens": trace.counts[TokenCategory.ASSISTANT_OUTPUT].count or 0,
                "total_tokens": trace.total or 0,
                "count_source": "estimated",
            },
            token_trace=trace,
        )

