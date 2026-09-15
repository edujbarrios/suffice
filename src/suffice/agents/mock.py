from __future__ import annotations

from suffice.agents.base import AgentAdapter
from suffice.config import ExperimentConfig
from suffice.models import AgentRunResult, Task
from suffice.tokens import EstimatedTokenCounter


class MockAgentAdapter(AgentAdapter):
    """Offline adapter that deterministically returns each task's expected value."""

    def run(self, task: Task, config: ExperimentConfig) -> AgentRunResult:
        counter = EstimatedTokenCounter()
        input_tokens = counter.count(config.system_prompt).count or 0
        input_tokens += counter.count(task.input).count or 0
        output = task.expected
        output_tokens = counter.count(str(output)).count or 0
        return AgentRunResult(
            output=output,
            metadata={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "count_source": "estimated",
            },
        )

