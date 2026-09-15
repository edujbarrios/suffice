from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when an experiment configuration is invalid."""


@dataclass(frozen=True)
class ModelConfig:
    provider: str = "mock"
    model: str = "deterministic"
    temperature: float = 0.0
    max_tokens: int = 1024
    base_url: str | None = None
    api_key_env: str | None = "OPENAI_API_KEY"
    timeout_seconds: float = 30.0
    retries: int = 2


@dataclass(frozen=True)
class OptimizationConfig:
    minimum_success_rate: float = 1.0
    maximum_success_drop: float = 0.0


@dataclass(frozen=True)
class ExperimentConfig:
    name: str
    tasks_path: Path
    output_directory: Path = Path("runs")
    seed: int = 42
    system_prompt: str = "Answer the task correctly and concisely."
    model: ModelConfig = field(default_factory=ModelConfig)
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)
    token_budgets: tuple[int, ...] = ()
    history_tail: int | None = None
    retrieval_top_k: int | None = None
    context_budget: int | None = None
    tool_description_mode: str = "full"
    tool_output_mode: str = "full"

    @classmethod
    def from_yaml(cls, path: str | Path) -> ExperimentConfig:
        config_path = Path(path)
        try:
            raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError) as exc:
            raise ConfigError(f"Could not read configuration: {exc}") from exc
        if not isinstance(raw, dict) or not raw.get("name") or not raw.get("tasks"):
            raise ConfigError("Configuration requires non-empty 'name' and 'tasks' fields")
        model_data = _mapping(raw.get("model", {}), "model")
        if "api_key" in model_data:
            raise ConfigError("Raw API keys are not allowed in YAML; use model.api_key_env instead")
        optimization_data = _mapping(raw.get("optimization", {}), "optimization")
        model = ModelConfig(**model_data)
        optimization = OptimizationConfig(**optimization_data)
        if not 0 <= optimization.minimum_success_rate <= 1:
            raise ConfigError("minimum_success_rate must be between 0 and 1")
        if model.max_tokens <= 0:
            raise ConfigError("model.max_tokens must be positive")
        if model.timeout_seconds <= 0 or model.retries < 0:
            raise ConfigError("model timeout must be positive and retries non-negative")
        budgets = tuple(int(value) for value in raw.get("token_budgets", ()))
        if any(value <= 0 for value in budgets):
            raise ConfigError("token_budgets must contain positive integers")
        tasks_path = Path(raw["tasks"])
        if not tasks_path.is_absolute():
            tasks_path = config_path.parent / tasks_path
        output = Path(raw.get("output_directory", "runs"))
        if not output.is_absolute():
            output = config_path.parent / output
        return cls(
            name=str(raw["name"]),
            tasks_path=tasks_path,
            output_directory=output,
            seed=int(raw.get("seed", 42)),
            system_prompt=str(raw.get("system_prompt", cls.system_prompt)),
            model=model,
            optimization=optimization,
            token_budgets=budgets,
            history_tail=_optional_positive(raw.get("history_tail"), "history_tail"),
            retrieval_top_k=_optional_positive(raw.get("retrieval_top_k"), "retrieval_top_k"),
            context_budget=_optional_positive(raw.get("context_budget"), "context_budget"),
            tool_description_mode=str(raw.get("tool_description_mode", "full")),
            tool_output_mode=str(raw.get("tool_output_mode", "full")),
        )


def _mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"'{field_name}' must be a mapping")
    return value


def _optional_positive(value: Any, field_name: str) -> int | None:
    if value is None:
        return None
    parsed = int(value)
    if parsed < 0:
        raise ConfigError(f"{field_name} must be non-negative")
    return parsed
