from __future__ import annotations

from pathlib import Path

from suffice.agents.mock import MockAgentAdapter
from suffice.agents.openai_compatible import OpenAICompatibleAgentAdapter
from suffice.config import ExperimentConfig
from suffice.evaluators import evaluate
from suffice.models import ExperimentResult
from suffice.runs import save_run
from suffice.tasks import load_tasks


class Experiment:
    def __init__(self, config: ExperimentConfig):
        self.config = config

    @classmethod
    def from_yaml(cls, path: str | Path) -> Experiment:
        return cls(ExperimentConfig.from_yaml(path))

    def run(self, *, save: bool = False) -> ExperimentResult:
        adapters = {
            "mock": MockAgentAdapter,
            "openai_compatible": OpenAICompatibleAgentAdapter,
        }
        try:
            agent = adapters[self.config.model.provider]()
        except KeyError as exc:
            raise ValueError(f"Unsupported provider: {self.config.model.provider}") from exc
        cases = []
        for task in load_tasks(self.config.tasks_path):
            result = agent.run(task, self.config)
            result.success = evaluate(task.evaluation, result.output, task.expected)
            result.metadata["task_id"] = task.id
            cases.append(result)
        experiment_result = ExperimentResult(cases)
        if save:
            save_run(self.config, experiment_result)
        return experiment_result

