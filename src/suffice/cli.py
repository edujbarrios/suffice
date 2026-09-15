from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from suffice.config import ConfigError, ExperimentConfig
from suffice.experiment import Experiment


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="suffice", description="Token efficiency for AI agents")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "run"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("config")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "validate":
            config = ExperimentConfig.from_yaml(args.config)
            print(f"Valid: {config.name}")
            return 0
        result = Experiment.from_yaml(args.config).run(save=True)
        print(json.dumps({"success_rate": result.success_rate, "cases": len(result.cases)}))
        return 0
    except (ConfigError, OSError, ValueError) as exc:
        print(f"Error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

