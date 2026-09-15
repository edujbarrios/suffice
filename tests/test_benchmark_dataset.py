from collections import Counter
from pathlib import Path

from suffice.tasks import load_tasks


def test_llm7_benchmark_is_balanced_and_traceable() -> None:
    root = Path(__file__).parents[1]
    tasks = load_tasks(root / "benchmarks/llm7_context_efficiency_v1.jsonl")
    assert len(tasks) == 60
    assert len({task.id for task in tasks}) == 60
    assert Counter(task.metadata["category"] for task in tasks) == {
        "factual": 15,
        "calculation": 15,
        "extraction": 15,
        "distractor_context": 15,
    }
    assert all(task.metadata["source"] == "ai_generated" for task in tasks)
    assert {task.evaluation for task in tasks} <= {"exact_match", "numeric"}


def test_llm7_config_uses_complete_benchmark() -> None:
    root = Path(__file__).parents[1]
    text = (root / "examples/llm7.yaml").read_text(encoding="utf-8")
    assert "llm7_context_efficiency_v1.jsonl" in text
