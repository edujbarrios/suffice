from __future__ import annotations

import os
import time
from typing import Any

from suffice.agents.base import AgentAdapter
from suffice.config import ExperimentConfig
from suffice.models import AgentRunResult, Task
from suffice.tokens import CountSource, TokenCategory, TokenCount, TokenTrace


class OpenAICompatibleAgentAdapter(AgentAdapter):
    def __init__(self, client: Any | None = None):
        self.client = client

    def run(self, task: Task, config: ExperimentConfig) -> AgentRunResult:
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise RuntimeError("Install Suffice with the 'openai' extra") from exc
        api_key = os.environ.get(config.model.api_key_env)
        if not api_key:
            raise ValueError(f"Missing API key environment variable: {config.model.api_key_env}")
        base_url = (config.model.base_url or "https://api.openai.com/v1").rstrip("/")
        payload = {
            "model": config.model.model,
            "messages": [
                {"role": "system", "content": config.system_prompt},
                {"role": "user", "content": task.input},
            ],
            "temperature": config.model.temperature,
            "max_tokens": config.model.max_tokens,
        }
        client = self.client or httpx.Client(timeout=config.model.timeout_seconds)
        started = time.perf_counter()
        response = None
        for attempt in range(config.model.retries + 1):
            try:
                response = client.post(
                    f"{base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json=payload,
                )
                response.raise_for_status()
                break
            except (httpx.TimeoutException, httpx.TransportError):
                if attempt == config.model.retries:
                    raise
        data = response.json()
        output = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        trace = TokenTrace()
        trace.record(
            TokenCategory.SYSTEM,
            TokenCount(usage.get("prompt_tokens"), CountSource.PROVIDER_REPORTED),
        )
        trace.record(
            TokenCategory.ASSISTANT_OUTPUT,
            TokenCount(usage.get("completion_tokens"), CountSource.PROVIDER_REPORTED),
        )
        details = usage.get("completion_tokens_details", {})
        if "reasoning_tokens" in details:
            trace.record(
                TokenCategory.REASONING,
                TokenCount(details["reasoning_tokens"], CountSource.PROVIDER_REPORTED),
            )
        return AgentRunResult(
            output=output,
            latency_ms=(time.perf_counter() - started) * 1000,
            metadata={"provider_usage": usage, "total_tokens": usage.get("total_tokens", trace.total)},
            token_trace=trace,
        )
