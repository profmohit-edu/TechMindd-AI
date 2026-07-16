"""Provider failover, generation accounting, and per-run budget enforcement."""

from __future__ import annotations

import logging
import queue
import threading
import time
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from observability.metrics import (
    PROVIDER_COST,
    PROVIDER_LATENCY,
    PROVIDER_REQUESTS,
    PROVIDER_TOKENS,
)


LOGGER = logging.getLogger("techmindd.providers.failover")

_TRANSIENT_MARKERS = (
    "timeout",
    "timed out",
    "rate limit",
    "rate_limit",
    "quota",
    "unavailable",
    "connection",
    "temporar",
    "transient",
    "overloaded",
    "resource exhausted",
    "503",
    "429",
)

# USD per one million input/output tokens. Unknown models intentionally use
# zero-cost rates unless callers provide an explicit override.
_DEFAULT_COST_RATES: dict[tuple[str, str], tuple[float, float]] = {
    ("openai", "gpt-4o-mini"): (0.15, 0.60),
    ("gemini", "gemini-1.5-flash"): (0.075, 0.30),
    ("gemini", "gemini-2.5-flash"): (0.30, 2.50),
}


class ProviderFailoverError(RuntimeError):
    """Raised after all permitted providers fail with retryable errors."""


class BudgetExceededError(RuntimeError):
    """Raised when a configured per-run token or cost budget is exceeded."""


@dataclass(frozen=True)
class GenerationRecord:
    """Metrics for one successful logical generation request."""

    provider_used: str
    provider_fallback: str | None
    retries: int
    latency: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: float
    model: str


class ProviderManager:
    """Provider-compatible facade with ordered failover and run accounting."""

    def __init__(
        self,
        providers: Sequence[tuple[str, Any]],
        *,
        max_retries: int = 1,
        request_timeout_seconds: float = 60.0,
        token_budget: int | None = None,
        cost_budget: float | None = None,
        cost_rates: Mapping[tuple[str, str], tuple[float, float]] | None = None,
    ) -> None:
        if not providers:
            raise ValueError("at least one provider is required")
        if max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        if request_timeout_seconds <= 0:
            raise ValueError("request_timeout_seconds must be greater than 0")
        if token_budget is not None and token_budget <= 0:
            raise ValueError("token_budget must be greater than 0")
        if cost_budget is not None and cost_budget <= 0:
            raise ValueError("cost_budget must be greater than 0")

        self._providers = list(providers)
        self._max_retries = max_retries
        self._request_timeout_seconds = request_timeout_seconds
        self._token_budget = token_budget
        self._cost_budget = cost_budget
        self._cost_rates = dict(_DEFAULT_COST_RATES)
        if cost_rates:
            self._cost_rates.update(cost_rates)
        self._records: list[GenerationRecord] = []
        self._metrics_lock = threading.Lock()
        self._provider_locks = {name: threading.Lock() for name, _ in self._providers}

        self.model = str(getattr(self._providers[0][1], "model", "unknown"))

    @property
    def last_usage(self) -> dict[str, int]:
        """Return aggregate usage using the legacy provider attribute shape."""
        summary = self.summary()
        return {
            "input_tokens": int(summary["input_tokens"]),
            "output_tokens": int(summary["output_tokens"]),
            "total_tokens": int(summary["total_tokens"]),
        }

    @property
    def generation_records(self) -> list[dict[str, Any]]:
        """Return a snapshot of per-generation provider metrics."""
        with self._metrics_lock:
            return [asdict(record) for record in self._records]

    def generate_structured_json(self, **request: Any) -> dict[str, Any]:
        """Generate JSON, moving to the next provider on retryable failures."""
        self._ensure_budget_available()
        started = time.monotonic()
        last_error: Exception | None = None
        maximum_attempts = min(len(self._providers), self._max_retries + 1)

        for attempt, (provider_name, provider) in enumerate(self._providers[:maximum_attempts]):
            try:
                # Existing adapters honor this attribute for their SDK requests.
                provider.timeout_seconds = min(
                    float(getattr(provider, "timeout_seconds", self._request_timeout_seconds)),
                    self._request_timeout_seconds,
                )
                result, usage = self._invoke_provider(provider_name, provider, request)

                record = self._build_record(
                    provider_name=provider_name,
                    provider=provider,
                    usage=usage,
                    retries=attempt,
                    latency=time.monotonic() - started,
                )
                self._record_and_enforce_budget(record)
                PROVIDER_REQUESTS.labels(provider_name, "success").inc()
                PROVIDER_LATENCY.labels(provider_name).observe(record.latency)
                PROVIDER_TOKENS.labels(provider_name, "input").inc(record.input_tokens)
                PROVIDER_TOKENS.labels(provider_name, "output").inc(record.output_tokens)
                PROVIDER_COST.labels(provider_name).inc(record.estimated_cost)
                LOGGER.info(
                    "Generation completed with provider=%s fallback=%s retries=%d latency=%.3fs tokens=%d cost=%.6f",
                    record.provider_used,
                    record.provider_fallback,
                    record.retries,
                    record.latency,
                    record.total_tokens,
                    record.estimated_cost,
                )
                return result
            except BudgetExceededError:
                raise
            except Exception as exc:  # noqa: BLE001
                if not self._is_retryable(exc):
                    PROVIDER_REQUESTS.labels(provider_name, "error").inc()
                    raise
                last_error = exc
                PROVIDER_REQUESTS.labels(provider_name, "retryable_error").inc()
                LOGGER.warning(
                    "Provider %s failed with retryable error; attempt=%d/%d error=%s",
                    provider_name,
                    attempt + 1,
                    maximum_attempts,
                    exc,
                )

        raise ProviderFailoverError(
            f"All {maximum_attempts} permitted provider attempts failed"
        ) from last_error

    def summary(self) -> dict[str, Any]:
        """Aggregate all generation metrics for package metadata."""
        with self._metrics_lock:
            records = list(self._records)

        used = list(dict.fromkeys(record.provider_used for record in records))
        fallbacks = list(
            dict.fromkeys(
                record.provider_fallback
                for record in records
                if record.provider_fallback is not None
            )
        )
        return {
            "provider_used": used,
            "provider_fallback": fallbacks,
            "retries": sum(record.retries for record in records),
            "latency": sum(record.latency for record in records),
            "input_tokens": sum(record.input_tokens for record in records),
            "output_tokens": sum(record.output_tokens for record in records),
            "total_tokens": sum(record.total_tokens for record in records),
            "estimated_cost": round(sum(record.estimated_cost for record in records), 8),
            "generations": [asdict(record) for record in records],
        }

    def _build_record(
        self,
        *,
        provider_name: str,
        provider: Any,
        usage: dict[str, Any],
        retries: int,
        latency: float,
    ) -> GenerationRecord:
        input_tokens = int(usage.get("input_tokens", 0) or 0)
        output_tokens = int(usage.get("output_tokens", 0) or 0)
        total_tokens = int(usage.get("total_tokens", input_tokens + output_tokens) or 0)
        model = str(getattr(provider, "model", "unknown"))
        input_rate, output_rate = self._cost_rates.get(
            (provider_name.lower(), model.lower()),
            (0.0, 0.0),
        )
        estimated_cost = (
            input_tokens * input_rate + output_tokens * output_rate
        ) / 1_000_000
        return GenerationRecord(
            provider_used=provider_name,
            provider_fallback=provider_name if retries else None,
            retries=retries,
            latency=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            model=model,
        )

    def _invoke_provider(
        self,
        provider_name: str,
        provider: Any,
        request: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Run one provider behind a hard manager-level response deadline."""
        outcome: queue.Queue[tuple[bool, Any, dict[str, Any]]] = queue.Queue(maxsize=1)

        def invoke() -> None:
            try:
                with self._provider_locks[provider_name]:
                    result = provider.generate_structured_json(**request)
                    usage = dict(getattr(provider, "last_usage", {}) or {})
                outcome.put((True, result, usage))
            except BaseException as exc:  # propagate provider failures to the caller thread
                outcome.put((False, exc, {}))

        worker = threading.Thread(
            target=invoke,
            name=f"techmindd-provider-{provider_name}",
            daemon=True,
        )
        worker.start()
        try:
            succeeded, value, usage = outcome.get(timeout=self._request_timeout_seconds)
        except queue.Empty as exc:
            raise TimeoutError(
                f"Provider {provider_name} exceeded request timeout of "
                f"{self._request_timeout_seconds:.2f}s"
            ) from exc
        if not succeeded:
            raise value
        return value, usage

    def _ensure_budget_available(self) -> None:
        summary = self.summary()
        if self._token_budget is not None and summary["total_tokens"] >= self._token_budget:
            raise BudgetExceededError("Per-run token budget has been exhausted")
        if self._cost_budget is not None and summary["estimated_cost"] >= self._cost_budget:
            raise BudgetExceededError("Per-run cost budget has been exhausted")

    def _record_and_enforce_budget(self, record: GenerationRecord) -> None:
        with self._metrics_lock:
            total_tokens = sum(item.total_tokens for item in self._records) + record.total_tokens
            total_cost = sum(item.estimated_cost for item in self._records) + record.estimated_cost
            if self._token_budget is not None and total_tokens > self._token_budget:
                raise BudgetExceededError(
                    f"Per-run token budget exceeded: {total_tokens} > {self._token_budget}"
                )
            if self._cost_budget is not None and total_cost > self._cost_budget:
                raise BudgetExceededError(
                    f"Per-run cost budget exceeded: {total_cost:.8f} > {self._cost_budget:.8f}"
                )
            self._records.append(record)

    @staticmethod
    def _is_retryable(error: Exception) -> bool:
        current: BaseException | None = error
        while current is not None:
            name = current.__class__.__name__.lower()
            message = str(current).lower()
            if any(marker in name or marker in message for marker in _TRANSIENT_MARKERS):
                return True
            current = current.__cause__ or current.__context__
        return False
