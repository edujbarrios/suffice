from __future__ import annotations

from abc import ABC, abstractmethod

from suffice.config import ExperimentConfig
from suffice.models import AgentRunResult, Task


class AgentAdapter(ABC):
    @abstractmethod
    def run(self, task: Task, config: ExperimentConfig) -> AgentRunResult: ...

