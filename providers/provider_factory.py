"""Factory for resolving and creating LLM providers."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import config
from providers.gemini_provider import GeminiProvider
from providers.openai_provider import OpenAIProvider


logger = logging.getLogger(__name__)


type Provider = Any


class ProviderFactory:
    """Resolve and lazily construct provider implementations."""

    def __init__(self) -> None:
        """Initialize the provider registry."""
        logger.info("Initializing ProviderFactory")
        self._registry: dict[str, Callable[[], Provider]] = {
            "openai": OpenAIProvider,
            "gemini": GeminiProvider,
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
        return self.get_provider(provider_name)

    def supported_providers(self) -> list[str]:
        """Return the list of provider names supported by this factory."""
        return sorted(self._registry.keys())
