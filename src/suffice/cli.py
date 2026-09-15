from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from suffice.config import ConfigError, ExperimentConfig
from suffice.experiment import Experiment
from suffice.experiments import budget_sweep
from suffice.metrics import efficiency_frontier, minimum_successful_token_budget


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="suffice", description="Token efficiency for AI agents")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "run"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("config")
    frontier = subparsers.add_parser("frontier")
    frontier.add_argument("config")
    compare = subparsers.add_parser("compare")
    compare.add_argument("baseline_run")
    compare.add_argument("candidate_run")
    report = subparsers.add_parser("report")
    report.add_argument("run_directory")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "validate":
            config = ExperimentConfig.from_yaml(args.config)
            print(f"Valid: {config.name}")
            return 0
        if args.command == "frontier":
            experiment = Experiment.from_yaml(args.config)
            sweep = budget_sweep(experiment.config)
            print(
                json.dumps(
                    {
                        "frontier": [asdict(point) for point in efficiency_frontier(sweep)],
                        "minimum_successful_token_budget": minimum_successful_token_budget(sweep),
                    }
                )
            )
            return 0
        if args.command == "compare":
            baseline = json.loads((Path(args.baseline_run) / "metrics.json").read_text())
            candidate = json.loads((Path(args.candidate_run) / "metrics.json").read_text())
            baseline_tokens = baseline["average_tokens_per_task"]
            candidate_tokens = candidate["average_tokens_per_task"]
            print(
                json.dumps(
                    {
                        "baseline_success_rate": baseline["success_rate"],
                        "candidate_success_rate": candidate["success_rate"],
                        "token_reduction": baseline_tokens - candidate_tokens,
                    }
                )
            )
            return 0
        if args.command == "report":
            report_path = Path(args.run_directory) / "report.html"
            if not report_path.exists():
                raise ValueError(f"Report not found: {report_path}")
            print(report_path.resolve())
            return 0
        result = Experiment.from_yaml(args.config).run(save=True)
        print(json.dumps({"success_rate": result.success_rate, "cases": len(result.cases)}))
        return 0
    except (ConfigError, OSError, ValueError) as exc:
        print(f"Error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
