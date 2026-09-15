from pathlib import Path

import pytest

from suffice.agents import MockAgentAdapter
from suffice.cli import main
from suffice.config import ConfigError, ExperimentConfig
from suffice.experiment import Experiment
from suffice.models import Task
from suffice.tokens import CountSource, EstimatedTokenCounter

ROOT = Path(__file__).parents[1]


def test_config_loads_relative_paths() -> None:
    config = ExperimentConfig.from_yaml(ROOT / "examples/baseline.yaml")
    assert config.name == "offline-baseline"
    assert config.tasks_path == ROOT / "examples/../benchmarks/smoke.jsonl"


def test_invalid_config(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("name: missing-tasks", encoding="utf-8")
    with pytest.raises(ConfigError):
        ExperimentConfig.from_yaml(path)


def test_estimated_count_has_explicit_provenance() -> None:
    count = EstimatedTokenCounter().count("abcdefgh")
    assert count.count == 2
    assert count.source is CountSource.ESTIMATED


def test_mock_is_deterministic() -> None:
    config = ExperimentConfig("test", Path("tasks.jsonl"))
    task = Task("one", "Question", "Answer")
    assert MockAgentAdapter().run(task, config) == MockAgentAdapter().run(task, config)


def test_experiment_and_cli(capsys: pytest.CaptureFixture[str]) -> None:
    path = ROOT / "examples/baseline.yaml"
    result = Experiment.from_yaml(path).run()
    assert result.success_rate == 1.0
    assert result.tokens_per_successful_task is not None
    assert main(["validate", str(path)]) == 0
    assert "Valid: offline-baseline" in capsys.readouterr().out

