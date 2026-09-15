# Suffice benchmark datasets

## llm7-context-efficiency-v1

This is a concrete benchmark for **short, deterministically verifiable answers
to questions containing direct instructions or distractor context**. It is not
a universal agent benchmark.

The dataset contains 60 balanced cases:

| Category | Cases | Purpose |
| --- | ---: | --- |
| Factual QA | 15 | Tests concise recall under an exact output contract |
| Calculation | 15 | Tests deterministic arithmetic and token metrics |
| Extraction | 15 | Tests selecting one value from structured records |
| Distractor context | 15 | Tests using relevant evidence while ignoring noise |

All benchmark prompts and expected answers were generated with AI assistance.
They are synthetic and have not been independently expert-reviewed. This is
disclosed in every task through `metadata.source = "ai_generated"`. The dataset
is suitable for demonstrating and testing the Suffice workflow, not for making
broad claims about model intelligence, safety, or production readiness.

### Evaluation

Answers use `exact_match` or `numeric` evaluation. The system prompt requests
only the answer, avoiding subjective grading. A run is reproducible only when
its model selector, endpoint, configuration, dataset revision, token-count
provenance, and timestamp are retained.

### Known limitations

- Most cases are easy and use short answers.
- Factual items may reward memorization.
- Synthetic phrasing is less varied than real user traffic.
- The dataset currently evaluates answer generation, not executable tool use.
- The `default` llm7.io selector may route differently over time; saved run
  metadata must be consulted before comparing results.

Contributions should add human review, paraphrase diversity, adversarial
distractors, and domain-specific suites rather than treating this dataset as
finished.

