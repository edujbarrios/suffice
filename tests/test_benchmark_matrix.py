import json
from pathlib import Path

import httpx
import pytest

from suffice.agents.openai_compatible import OpenAICompatibleAgentAdapter
from suffice.benchmark import BenchmarkConfigError, _load_matrix, run_benchmark_matrix
from suffice.config import ExperimentConfig, ModelConfig
from suffice.models import AgentRunResult, Task
from suffice.tokens import CountSource, TokenCategory, TokenCount, TokenTrace


def test_llm7_matrix_has_multiple_models_and_equivalent_agents() -> None:
    root = Path(__file__).parents[1]
    matrix = _load_matrix(root / "examples/llm7_matrix.yaml")
    assert len([model for model in matrix["models"] if model.get("enabled", True)]) >= 2
    assert {agent["id"] for agent in matrix["agents"]} == {"baseline", "compact"}
    assert matrix["tasks"].endswith("llm7_context_efficiency_v1.jsonl")


def test_matrix_rejects_missing_fields(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("name: incomplete", encoding="utf-8")
    with pytest.raises(BenchmarkConfigError):
        _load_matrix(path)


def test_adapter_records_resolved_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KEY", "secret")
    response = httpx.Response(
        200,
        request=httpx.Request("POST", "https://example.test/v1/chat/completions"),
        json={
            "model": "provider-resolved-model",
            "choices": [{"message": {"content": "Oslo"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 1, "total_tokens": 6},
        },
    )

    class Client:
        def post(self, *args: object, **kwargs: object) -> httpx.Response:
            return response

    config = ExperimentConfig(
        "resolved",
        Path("tasks"),
        model=ModelConfig(provider="openai_compatible", api_key_env="KEY"),
    )
    result = OpenAICompatibleAgentAdapter(Client()).run(Task("x", "q", "Oslo"), config)
    assert result.metadata["resolved_model"] == "provider-resolved-model"


def test_matrix_runs_every_model_agent_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tasks = tmp_path / "tasks.jsonl"
    tasks.write_text('{"id":"one","input":"q","expected":"a"}\n', encoding="utf-8")
    matrix = tmp_path / "matrix.yaml"
    matrix.write_text(
        """name: matrix
tasks: tasks.jsonl
output_directory: runs
provider:
  base_url: https://example.test/v1
  api_key_env: KEY
models:
  - {id: one, selector: model-one}
  - {id: two, selector: model-two}
agents:
  - {id: baseline, system_prompt: baseline}
  - {id: compact, system_prompt: compact}
""",
        encoding="utf-8",
    )

    class FakeAdapter:
        def run(self, task: Task, config: ExperimentConfig) -> AgentRunResult:
            return AgentRunResult(
                output=task.expected,
                metadata={"resolved_model": f"resolved-{config.model.model}"},
                token_trace=TokenTrace(
                    {TokenCategory.USER: TokenCount(3, CountSource.PROVIDER_REPORTED)}
                ),
            )

    monkeypatch.setattr("suffice.experiment.OpenAICompatibleAgentAdapter", FakeAdapter)
    directory = run_benchmark_matrix(matrix)
    summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
    assert len(summary["entries"]) == 4
    assert {entry["requested_model"] for entry in summary["entries"]} == {
        "model-one",
        "model-two",
    }
