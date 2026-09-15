from __future__ import annotations

import json
import re
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from suffice.config import ExperimentConfig
from suffice.metrics import calculate_metrics
from suffice.models import ExperimentResult
from suffice.reporting import render_html_report

SECRET_PATTERN = re.compile(r"(api[_-]?key|access[_-]?token|secret|password)", re.IGNORECASE)


def redact_secrets(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if SECRET_PATTERN.search(str(key)) else redact_secrets(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    return value


def save_run(config: ExperimentConfig, result: ExperimentResult) -> Path:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    directory = config.output_directory / run_id
    directory.mkdir(parents=True, exist_ok=False)
    config_data = redact_secrets(asdict(config))
    config_data["tasks_path"] = str(config.tasks_path)
    config_data["output_directory"] = str(config.output_directory)
    (directory / "config.yaml").write_text(
        yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8"
    )
    manifest = {"run_id": run_id, "experiment": config.name, "schema_version": 1}
    _write_json(directory / "manifest.json", manifest)
    with (directory / "cases.jsonl").open("w", encoding="utf-8") as stream:
        for case in result.cases:
            data = {
                "task_id": case.metadata.get("task_id"),
                "success": case.success,
                "output": case.output,
                "latency_ms": case.latency_ms,
                "tool_calls": case.tool_calls,
                "error": case.error,
                "token_trace": case.token_trace.to_dict(),
            }
            stream.write(json.dumps(redact_secrets(data), sort_keys=True) + "\n")
    metrics = asdict(calculate_metrics(result))
    _write_json(directory / "metrics.json", metrics)
    (directory / "report.html").write_text(
        render_html_report(config.name, metrics, result.cases), encoding="utf-8"
    )
    return directory


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
