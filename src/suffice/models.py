from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from suffice.tokens import TokenTrace


@dataclass(frozen=True)
class Task:
    id: str
    input: str
    expected: Any
    evaluation: str = "exact_match"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentRunResult:
    output: Any
    success: bool = False
    latency_ms: float = 0.0
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    token_trace: TokenTrace = field(default_factory=TokenTrace)


@dataclass
class ExperimentResult:
    cases: list[AgentRunResult]

    @property
    def success_rate(self) -> float:
        return sum(case.success for case in self.cases) / len(self.cases) if self.cases else 0.0

    @property
    def tokens_per_successful_task(self) -> float | None:
        successful = [case for case in self.cases if case.success]
        if not successful:
            return None
        return sum(case.metadata.get("total_tokens", 0) for case in successful) / len(successful)

