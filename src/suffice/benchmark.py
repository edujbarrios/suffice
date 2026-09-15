from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from suffice.config import ExperimentConfig, ModelConfig, OptimizationConfig
from suffice.experiment import Experiment
from suffice.metrics import calculate_metrics
from suffice.runs import save_run


class BenchmarkConfigError(ValueError):
    """Raised when a benchmark matrix is invalid."""


def run_benchmark_matrix(path: str | Path) -> Path:
    matrix_path = Path(path)
    raw = _load_matrix(matrix_path)
    tasks = _relative_path(matrix_path, raw["tasks"])
    output = _relative_path(matrix_path, raw.get("output_directory", "../runs"))
    provider = raw["provider"]
    models = [item for item in raw["models"] if item.get("enabled", True)]
    agents = [item for item in raw["agents"] if item.get("enabled", True)]
    if len(models) < 2 or len(agents) < 2:
        raise BenchmarkConfigError("A comparison matrix requires at least two models and agents")

    entries: list[dict[str, Any]] = []
    for model in models:
        for agent in agents:
            config = ExperimentConfig(
                name=f"{raw['name']}--{model['id']}--{agent['id']}",
                tasks_path=tasks,
                output_directory=output,
                seed=int(raw.get("seed", 42)),
                system_prompt=agent["system_prompt"],
                model=ModelConfig(
                    provider="openai_compatible",
                    model=model["selector"],
                    base_url=provider["base_url"],
                    api_key_env=provider["api_key_env"],
                    temperature=float(agent.get("temperature", 0)),
                    max_tokens=int(agent.get("max_tokens", 128)),
                    timeout_seconds=float(provider.get("timeout_seconds", 60)),
                    retries=int(provider.get("retries", 2)),
                ),
                optimization=OptimizationConfig(
                    minimum_success_rate=float(raw.get("minimum_success_rate", 0.95)),
                    maximum_success_drop=float(raw.get("maximum_success_drop", 0.01)),
                ),
            )
            result = Experiment(config).run()
            run_directory = save_run(config, result)
            resolved = sorted(
                {
                    str(case.metadata.get("resolved_model"))
                    for case in result.cases
                    if case.metadata.get("resolved_model")
                }
            )
            entries.append(
                {
                    "agent": agent["id"],
                    "requested_model": model["selector"],
                    "resolved_models": resolved,
                    "run_directory": str(run_directory),
                    "metrics": asdict(calculate_metrics(result)),
                }
            )

    directory = output / "benchmarks" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    directory.mkdir(parents=True, exist_ok=False)
    summary = {
        "name": raw["name"],
        "dataset": str(tasks),
        "disclosure": "Benchmark content was generated with AI assistance.",
        "entries": entries,
    }
    (directory / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    return directory


def _load_matrix(path: Path) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise BenchmarkConfigError(f"Could not read benchmark matrix: {exc}") from exc
    required = ("name", "tasks", "provider", "models", "agents")
    if not isinstance(raw, dict) or any(not raw.get(key) for key in required):
        raise BenchmarkConfigError(f"Benchmark matrix requires: {', '.join(required)}")
    if not isinstance(raw["provider"], dict):
        raise BenchmarkConfigError("provider must be a mapping")
    return raw


def _relative_path(config_path: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else config_path.parent / path
