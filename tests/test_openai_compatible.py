import json
from pathlib import Path

import httpx
import pytest

from suffice.agents import OpenAICompatibleAgentAdapter
from suffice.config import ExperimentConfig, ModelConfig
from suffice.models import Task
from suffice.tokens import CountSource, TokenCategory


def test_adapter_parses_provider_usage(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer test-secret"
        body = json.loads(request.content)
        assert body["model"] == "local-model"
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "Oslo"}}],
                "usage": {"prompt_tokens": 12, "completion_tokens": 2, "total_tokens": 14},
            },
        )

    monkeypatch.setenv("SUFFICE_TEST_KEY", "test-secret")
    client = httpx.Client(transport=httpx.MockTransport(handler))
    config = ExperimentConfig(
        "api",
        Path("tasks"),
        model=ModelConfig(
            provider="openai_compatible",
            model="local-model",
            base_url="http://local.test/v1",
            api_key_env="SUFFICE_TEST_KEY",
        ),
    )
    result = OpenAICompatibleAgentAdapter(client).run(Task("x", "Capital?", "Oslo"), config)
    assert result.output == "Oslo"
    assert result.token_trace.total == 14
    assert result.token_trace.counts[TokenCategory.SYSTEM].source is CountSource.PROVIDER_REPORTED


def test_adapter_requires_environment_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MISSING_KEY", raising=False)
    config = ExperimentConfig(
        "api",
        Path("tasks"),
        model=ModelConfig(provider="openai_compatible", api_key_env="MISSING_KEY"),
    )
    with pytest.raises(ValueError, match="Missing API key"):
        OpenAICompatibleAgentAdapter().run(Task("x", "q", "a"), config)


def test_local_endpoint_can_omit_authentication() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "authorization" not in request.headers
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "Oslo"}}],
                "usage": {"prompt_tokens": 8, "completion_tokens": 2, "total_tokens": 10},
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    config = ExperimentConfig(
        "local",
        Path("tasks"),
        model=ModelConfig(
            provider="openai_compatible",
            model="local-model",
            base_url="http://127.0.0.1:8000/v1",
            api_key_env=None,
        ),
    )
    result = OpenAICompatibleAgentAdapter(client).run(Task("x", "Capital?", "Oslo"), config)
    assert result.output == "Oslo"


def test_raw_api_key_is_rejected_from_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "unsafe.yaml"
    config_path.write_text(
        """name: unsafe
tasks: tasks.jsonl
model:
  provider: openai_compatible
  api_key: should-not-be-here
""",
        encoding="utf-8",
    )
    from suffice.config import ConfigError

    with pytest.raises(ConfigError, match="Raw API keys are not allowed"):
        ExperimentConfig.from_yaml(config_path)
