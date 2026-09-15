from pathlib import Path

from suffice.config import ExperimentConfig


def test_llm7_example_references_environment_variable() -> None:
    root = Path(__file__).parents[1]
    config = ExperimentConfig.from_yaml(root / "examples/llm7.yaml")
    assert config.model.base_url == "https://api.llm7.io/v1"
    assert config.model.api_key_env == "LLM7_API_KEY"
    assert config.model.model == "default"


def test_example_env_contains_no_real_credential() -> None:
    root = Path(__file__).parents[1]
    content = (root / ".env.example").read_text(encoding="utf-8")
    assert "replace-with-your-llm7-token" in content
