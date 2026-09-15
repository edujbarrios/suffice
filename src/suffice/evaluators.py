from __future__ import annotations

import json
import math
from abc import ABC, abstractmethod
from typing import Any


class Evaluator(ABC):
    @abstractmethod
    def evaluate(self, actual: Any, expected: Any) -> bool: ...


class ExactMatchEvaluator(Evaluator):
    def evaluate(self, actual: Any, expected: Any) -> bool:
        return str(actual).strip().casefold() == str(expected).strip().casefold()


class ContainsEvaluator(Evaluator):
    def evaluate(self, actual: Any, expected: Any) -> bool:
        return str(expected).strip().casefold() in str(actual).casefold()


class StructuredEvaluator(Evaluator):
    def evaluate(self, actual: Any, expected: Any) -> bool:
        if isinstance(actual, str):
            try:
                actual = json.loads(actual)
            except json.JSONDecodeError:
                return False
        return actual == expected


class NumericEvaluator(Evaluator):
    def __init__(self, tolerance: float = 1e-9):
        self.tolerance = tolerance

    def evaluate(self, actual: Any, expected: Any) -> bool:
        try:
            return math.isclose(float(actual), float(expected), abs_tol=self.tolerance)
        except (TypeError, ValueError):
            return False


EVALUATORS: dict[str, Evaluator] = {
    "exact_match": ExactMatchEvaluator(),
    "contains": ContainsEvaluator(),
    "structured": StructuredEvaluator(),
    "numeric": NumericEvaluator(),
}


def evaluate(name: str, actual: Any, expected: Any) -> bool:
    try:
        evaluator = EVALUATORS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown evaluator: {name}") from exc
    return evaluator.evaluate(actual, expected)
