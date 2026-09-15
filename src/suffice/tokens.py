from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from enum import Enum


class CountSource(str, Enum):
    PROVIDER_REPORTED = "provider_reported"
    EXACT_TOKENIZER = "exact_tokenizer"
    ESTIMATED = "estimated"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class TokenCount:
    count: int | None
    source: CountSource


class TokenCategory(str, Enum):
    SYSTEM = "system"
    USER = "user"
    HISTORY = "history"
    CONTEXT = "context"
    MEMORY = "memory"
    RETRIEVAL = "retrieval"
    TOOLS = "tools"
    TOOL_OUTPUT = "tool_output"
    ASSISTANT_INTERMEDIATE = "assistant_intermediate"
    ASSISTANT_OUTPUT = "assistant_output"
    CACHED_INPUT = "cached_input"
    REASONING = "reasoning"


@dataclass
class TokenTrace:
    counts: dict[TokenCategory, TokenCount] = field(default_factory=dict)

    def record(self, category: TokenCategory, count: TokenCount) -> None:
        self.counts[category] = count

    @property
    def total(self) -> int | None:
        available = [item.count for item in self.counts.values() if item.count is not None]
        return sum(available) if available else None

    @property
    def input_total(self) -> int:
        output = {TokenCategory.ASSISTANT_OUTPUT, TokenCategory.ASSISTANT_INTERMEDIATE}
        return sum(item.count or 0 for key, item in self.counts.items() if key not in output)

    def to_dict(self) -> dict[str, object]:
        return {
            "counts": {key.value: asdict(value) for key, value in self.counts.items()},
            "total": self.total,
        }


class TokenCounter(ABC):
    @abstractmethod
    def count(self, text: str) -> TokenCount: ...


class EstimatedTokenCounter(TokenCounter):
    """Deterministic approximation: one token per four UTF-8 characters."""

    def count(self, text: str) -> TokenCount:
        return TokenCount(max(1, (len(text) + 3) // 4) if text else 0, CountSource.ESTIMATED)
