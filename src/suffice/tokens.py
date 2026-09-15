from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum


class CountSource(StrEnum):
    PROVIDER_REPORTED = "provider_reported"
    EXACT_TOKENIZER = "exact_tokenizer"
    ESTIMATED = "estimated"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class TokenCount:
    count: int | None
    source: CountSource


class TokenCounter(ABC):
    @abstractmethod
    def count(self, text: str) -> TokenCount: ...


class EstimatedTokenCounter(TokenCounter):
    """Deterministic approximation: one token per four UTF-8 characters."""

    def count(self, text: str) -> TokenCount:
        return TokenCount(max(1, (len(text) + 3) // 4) if text else 0, CountSource.ESTIMATED)

