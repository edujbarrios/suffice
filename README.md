# Suffice

**Do the task. Use fewer tokens.**

Most agent benchmarks ask whether the task was completed. Suffice additionally
asks how many tokens were required to complete it.

AI agents spend tokens across system prompts, history, retrieved context, tool
schemas, tool results, intermediate output, and final answers. Suffice records
that lifecycle and compares configurations under one non-negotiable rule:

> Never optimize token usage independently of task success.

The objective is to minimize total tokens subject to task success meeting a
required quality threshold.

## Status

Suffice is an early-stage, provider-neutral Python toolkit. It includes an
offline deterministic mock so experiments and tests need no API key, network,
or GPU. Reported example results are generated locally and are not claims about
real models.

## Quick start

```bash
python -m pip install -e ".[dev]"
suffice validate examples/baseline.yaml
suffice run examples/baseline.yaml
```

```python
from suffice import Experiment

result = Experiment.from_yaml("examples/baseline.yaml").run()
print(result.success_rate)
print(result.tokens_per_successful_task)
```

Licensed under the [Mozilla Public License 2.0](LICENSE).

