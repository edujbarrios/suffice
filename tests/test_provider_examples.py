from pathlib import Path

from suffice.config import ExperimentConfig

ROOT = Path(__file__).parents[1]


def test_online_example_uses_environment_authentication() -> None:
    config = ExperimentConfig.from_yaml(ROOT / "examples/online_model.yaml")
    assert config.model.provider == "openai_compatible"
    assert config.model.api_key_env == "SUFFICE_API_KEY"
    assert config.model.base_url == "https://provider.example/v1"


def test_local_example_explicitly_omits_authentication() -> None:
    config = ExperimentConfig.from_yaml(ROOT / "examples/local_model.yaml")
    assert config.model.provider == "openai_compatible"
    assert config.model.api_key_env is None
    assert config.model.base_url == "http://127.0.0.1:8000/v1"


def test_example_env_never_contains_a_real_secret() -> None:
    content = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "replace-with-your-provider-key" in content
