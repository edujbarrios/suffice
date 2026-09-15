import json
from pathlib import Path

from suffice.config import ExperimentConfig
from suffice.experiment import Experiment
from suffice.runs import redact_secrets, save_run
from suffice.tokens import CountSource, TokenCategory, TokenCount, TokenTrace


def test_trace_preserves_category_and_provenance() -> None:
    trace = TokenTrace()
    trace.record(TokenCategory.SYSTEM, TokenCount(10, CountSource.EXACT_TOKENIZER))
    trace.record(TokenCategory.USER, TokenCount(4, CountSource.ESTIMATED))
    trace.record(TokenCategory.REASONING, TokenCount(None, CountSource.UNAVAILABLE))
    assert trace.total == 14
    assert trace.to_dict()["counts"]["user"]["source"] == CountSource.ESTIMATED


def test_artifacts_and_secret_redaction(tmp_path: Path) -> None:
    tasks = tmp_path / "tasks.jsonl"
    tasks.write_text('{"id":"x","input":"q","expected":"a"}\n', encoding="utf-8")
    config = ExperimentConfig("artifact", tasks, output_directory=tmp_path / "runs")
    result = Experiment(config).run()
    directory = save_run(config, result)
    assert {"config.yaml", "manifest.json", "cases.jsonl", "metrics.json"} <= {
        path.name for path in directory.iterdir()
    }
    case = json.loads((directory / "cases.jsonl").read_text(encoding="utf-8"))
    assert case["token_trace"]["total"] > 0
    assert redact_secrets({"api_key": "unsafe", "safe": "value"}) == {
        "api_key": "[REDACTED]",
        "safe": "value",
    }
