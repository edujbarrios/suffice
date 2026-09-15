from __future__ import annotations

from pathlib import Path

from suffice.agents.mock import MockAgentAdapter
from suffice.config import ExperimentConfig
from suffice.models import ExperimentResult
from suffice.tasks import load_tasks


class Experiment:
    def __init__(self, config: ExperimentConfig):
        self.config = config

    @classmethod
    def from_yaml(cls, path: str | Path) -> Experiment:
        return cls(ExperimentConfig.from_yaml(path))

    def run(self) -> ExperimentResult:
        if self.config.model.provider != "mock":
            raise ValueError(f"Unsupported provider: {self.config.model.provider}")
        agent = MockAgentAdapter()
        cases = []
        for task in load_tasks(self.config.tasks_path):
            result = agent.run(task, self.config)
            result.success = str(result.output).strip() == str(task.expected).strip()
            result.metadata["task_id"] = task.id
            cases.append(result)
        return ExperimentResult(cases)

