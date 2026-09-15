# Contributing to Suffice

Thank you for improving agent token efficiency without weakening task quality.

1. Open an issue for substantial behavior or schema changes.
2. Branch from current `main` and keep the change narrow.
3. Add deterministic tests needing no network, API key, or GPU.
4. Run `ruff check .`, `pytest`, and `python -m build`.
5. Explain token impact and quality impact in the pull request.

Never commit credentials or present estimates as provider-reported counts.
Benchmark claims must identify the model, config, dataset, and count provenance.
Contributions are licensed under MPL-2.0.

