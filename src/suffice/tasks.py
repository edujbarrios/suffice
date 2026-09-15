from __future__ import annotations

import json
from pathlib import Path

from suffice.models import Task


def load_tasks(path: str | Path) -> list[Task]:
    tasks: list[Task] = []
    with Path(path).open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                tasks.append(Task(**data))
            except (json.JSONDecodeError, TypeError) as exc:
                raise ValueError(f"Invalid task at line {line_number}: {exc}") from exc
    if not tasks:
        raise ValueError("Task dataset is empty")
    return tasks
