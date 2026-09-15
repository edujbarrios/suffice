import json
from pathlib import Path

from suffice.config import ExperimentConfig
from suffice.experiment import Experiment
from suffice.runs import save_run


def test_run_writes_json_and_safe_html(tmp_path: Path) -> None:
    tasks = tmp_path / "tasks.jsonl"
    tasks.write_text(
        '{"id":"safe","input":"q","expected":"<script>alert(1)</script>"}\n',
        encoding="utf-8",
    )
    config = ExperimentConfig("Report <demo>", tasks, output_directory=tmp_path / "runs")
    directory = save_run(config, Experiment(config).run())
    metrics = json.loads((directory / "metrics.json").read_text(encoding="utf-8"))
    report = (directory / "report.html").read_text(encoding="utf-8")
    assert metrics["success_rate"] == 1.0
    assert "Report &lt;demo&gt;" in report
    assert "<script>alert(1)</script>" not in report
    assert "PASS" in report
