# Suffice

**Do the task. Use fewer tokens.**

> **Suffice finds how few tokens an AI agent needs to successfully complete a
> task.**

It measures token usage across prompts, context, tools, memory, and final
responses, while ensuring that reducing tokens does not reduce task quality.

Most agent benchmarks ask whether the task was completed. Suffice additionally
asks how many tokens were required to complete it.

AI agents repeatedly pay for system prompts, conversation history, retrieved
context, memory, tool schemas, tool results, intermediate work, and final
answers. Suffice makes that consumption visible under one rule:

> Never optimize token usage independently of task success.

The objective is `minimize tokens` subject to
`task success >= required quality threshold`. A failed 200-token run is not
better than a successful 1,000-token run.

## Features

- Runs JSONL task suites through framework-neutral agent adapters.
- Tracks token categories with `provider_reported`, `exact_tokenizer`,
  `estimated`, or `unavailable` provenance.
- Evaluates exact, contains, structured, and numeric outputs deterministically.
- Calculates Minimum Successful Token Budget and Token Efficiency Frontier.
- Accepts candidates only under explicit quality constraints.
- Writes JSONL/JSON artifacts and a dependency-free static HTML report.
- Works offline through a deterministic mock adapter.
- Supports generic OpenAI-compatible chat-completions endpoints optionally.

Applications include system-prompt optimization, history trimming, retrieval
top-k tuning, tool-schema selection, tool-output compression, memory budgeting,
model comparison, final-answer budgeting, and context-window experiments.

## Install and run

Python 3.10 or newer is required.

```bash
python -m pip install -e ".[dev]"
suffice validate examples/baseline.yaml
suffice run examples/baseline.yaml
suffice frontier examples/frontier.yaml
```

Each saved run contains `config.yaml`, `manifest.json`, `cases.jsonl`,
`metrics.json`, and `report.html` under `runs/<run-id>/`.

```bash
suffice report runs/<run-id>
suffice compare runs/<baseline-id> runs/<candidate-id>
```

No API key, internet connection, or GPU is needed for bundled examples. Mock
results validate the harness; they are not evidence about real models.

## Python API

```python
from suffice import Experiment

result = Experiment.from_yaml("examples/baseline.yaml").run(save=True)
print(result.success_rate)
print(result.tokens_per_successful_task)
```

## Configuration

```yaml
name: prompt-budget-study
tasks: ../benchmarks/agent_efficiency.jsonl
seed: 42
system_prompt: Answer correctly and concisely.
model:
  provider: mock
  model: deterministic
  temperature: 0
  max_tokens: 128
token_budgets: [16, 32, 64, 128, 256]
optimization:
  minimum_success_rate: 0.95
  maximum_success_drop: 0.01
history_tail: 4
retrieval_top_k: 3
tool_description_mode: compact
tool_output_mode: structured
output_directory: ../runs
```

For compatible endpoints, use `provider: openai_compatible`, provide
`base_url`, and set `api_key_env` to an environment variable *name*. Secrets
are never accepted as config values. Install HTTP support with
`pip install -e ".[openai]"`.

### Running experiments with llm7.io

Suffice includes an llm7.io configuration because that service is being used
for the project's real-model experiments. This statement identifies the
experimental endpoint; it does not imply endorsement, partnership, or results
that have not been generated and committed reproducibly.

```bash
cp .env.example .env
# Set LLM7_API_KEY in .env, then run:
suffice validate examples/llm7.yaml
suffice run examples/llm7.yaml
suffice benchmark examples/llm7_matrix.yaml
```

On Windows PowerShell, copy the file with `Copy-Item .env.example .env`.
Suffice loads `.env` automatically. The bundled configuration uses the
documented `https://api.llm7.io/v1` endpoint and the `default` model selector.
The real `.env` file is ignored by Git; `.env.example` contains no credential.

For the CV-oriented experiment, `llm7_matrix.yaml` evaluates the same 60 tasks
with both `default` and `fast`, each under semantically equivalent `baseline`
and `compact` agent prompts. The optional paid `pro` selector is disabled by
default. This factorial design separates model choice from prompt overhead and
records the provider-resolved model alongside success, tokens, and latency.
Results are written beneath `runs/benchmarks/`; no result is bundled until it
has actually been generated.

## Token accounting and metrics

Traces recognize `system`, `user`, `history`, `context`, `memory`, `retrieval`,
`tools`, `tool_output`, `assistant_intermediate`, `assistant_output`,
`cached_input`, and `reasoning`. Categories are strings so stored traces can
evolve without positional schema migrations.

Provider usage is preferred. Future counters can supply exact tokenizer counts.
The fallback estimates one token per four characters and labels every count
`estimated`; unavailable provider fields are never silently presented as exact.

- **Task Success Rate**: successful cases divided by all cases.
- **Total Tokens per Task**: sum of available categories for one case.
- **Tokens per Successful Task**: mean over successful cases only, shown beside
  success rate; `null` when no case succeeds.
- **Input / Output Tokens**: measured non-output and assistant-output totals.
- **Tool Overhead**: tool schema plus tool-result tokens.
- **Context Overhead**: history, context, memory, and retrieval tokens.
- **Token Reduction**: `baseline - candidate`.
- **Token Reduction Percentage**: `(baseline - candidate) / baseline`.
- **Minimum Successful Token Budget**: smallest observed budget reaching the
  required success rate.
- **Token Efficiency Frontier**: observed `(budget, success, tokens)` points.

A candidate is accepted only when it reduces tokens, meets
`minimum_success_rate`, and stays within `maximum_success_drop`.

## Architecture

```text
JSONL tasks + YAML config
          │
          ▼
 AgentAdapter ── Mock / OpenAI-compatible
          │
          ▼
 AgentRunResult + TokenTrace
          │
          ├── deterministic Evaluator
          ├── Metrics / Comparison / Frontier
          └── JSON artifacts + static HTML
```

Adapters isolate providers, evaluators isolate correctness, and token counts
carry provenance. PyYAML is the only core runtime dependency. Suffice does not
depend on an agent framework or vector database.

## Benchmark

The repository contains two deliberately different datasets. The 12-case
offline smoke suite validates harness behavior with deterministic mock budgets.
The 60-case `llm7-context-efficiency-v1` suite is a concrete use case for short,
deterministically verifiable answers across factual QA, calculation, extraction,
and distractor context.

The 60 prompts and expected answers were generated with AI assistance and have
not yet received independent expert review. They are synthetic evaluation
content, not evidence of general model capability. See
[`benchmarks/README.md`](benchmarks/README.md) for composition, methodology, and
limitations. Do not draw research or production conclusions without further
human review and domain-specific cases.

## Reproduce from a fresh clone

```bash
git clone https://github.com/edujbarrios/suffice.git
cd suffice
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[dev]"
ruff check .
pytest
python -m build
suffice validate examples/frontier.yaml
suffice frontier examples/frontier.yaml
suffice run examples/baseline.yaml
```

## Limitations and roadmap

Suffice is intentionally not a complete, universal benchmark. Every real use
case has different tasks, success criteria, tools, context sources, and token
constraints; answering the central question rigorously therefore requires a
benchmark designed or adapted for that use case. The project provides a solid,
reproducible foundation on which those domain-specific experiments can be
built.

Version 0.1 exposes deterministic controls and a smoke benchmark for validating
the harness. It does not yet rewrite prompts, semantically prune context, run
external tools, or provide a universal exact tokenizer. Provider usage fields
also differ.

The principal future direction is an **Agent Token Optimizer**:

```text
baseline → benchmark → locate largest token sources
         → propose smaller configurations → evaluate
         → keep only candidates that preserve quality
```

Future work includes prompt compression, semantic pruning, adaptive retrieval,
memory/tool-output compression, dynamic budgets, cache-aware analysis, routing,
latency/energy/cost measurement, and Pareto analysis. The eventual question is:
*What is the cheapest token configuration that still achieves 95% success?*

## Open source

Copyright © 2026 Eduardo J. Barrios. Suffice is licensed under the
[Mozilla Public License 2.0](LICENSE). See [CONTRIBUTING.md](CONTRIBUTING.md),
[SECURITY.md](SECURITY.md), and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

