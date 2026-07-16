"""Factory for resolving and creating LLM providers."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, Sequence

import config
from providers.failover import ProviderManager

logger = logging.getLogger(__name__)


type Provider = Any


def _openai_provider() -> Provider:
    from providers.openai_provider import OpenAIProvider

    return OpenAIProvider()


def _gemini_provider() -> Provider:
    from providers.gemini_provider import GeminiProvider

    return GeminiProvider()


class ProviderFactory:
    """Resolve and lazily construct provider implementations."""

    def __init__(self) -> None:
        """Initialize the provider registry."""
        logger.info("Initializing ProviderFactory")
        self._registry: dict[str, Callable[[], Provider]] = {
            "openai": _openai_provider,
            "gemini": _gemini_provider,
        }

    def get_provider(self, provider_name: str) -> Provider:
        """Return a provider instance for the requested provider name."""
        key = provider_name.strip().lower()
        provider_builder = self._registry.get(key)
        if provider_builder is None:
            raise ValueError(f"Unsupported provider: {provider_name}")

        logger.info("Creating provider: %s", key)
        return provider_builder()

    def default_provider(self) -> Provider:
        """Return the default provider instance resolved from configuration."""
        configured_name = getattr(config.settings, "provider", "openai")
        provider_name = str(configured_name).strip().lower() or "openai"
        if provider_name == "auto":
            return self.managed_provider()
        return self.get_provider(provider_name)

    def managed_provider(self, priority: Sequence[str] | None = None) -> ProviderManager:
        """Build the configured ordered provider chain."""
        providers: list[tuple[str, Provider]] = []
        provider_priority = (
            tuple(priority) if priority is not None else config.settings.provider_priority
        )
        for provider_name in provider_priority:
            if provider_name not in self._registry:
                logger.warning("Skipping unsupported provider in priority list: %s", provider_name)
                continue
            try:
                providers.append((provider_name, self.get_provider(provider_name)))
            except (
                Exception
            ) as exc:  # provider configuration errors are non-fatal when alternatives exist
                logger.warning("Skipping unavailable provider %s: %s", provider_name, exc)

        if not providers:
            raise ValueError("No configured providers are available")

        return ProviderManager(
            providers,
            max_retries=config.settings.provider_max_retries,
            request_timeout_seconds=config.settings.provider_request_timeout_seconds,
            token_budget=config.settings.run_token_budget,
            cost_budget=config.settings.run_cost_budget,
        )

    def supported_providers(self) -> list[str]:
        """Return the list of provider names supported by this factory."""
        return sorted(self._registry.keys())
