"""Factory for resolving and creating LLM providers."""

from __future__ import annotations

import logging
from typing import Any

import config
import providers
from plugins.discovery import classes_defined_in_package, import_package_modules
from providers.provider import BaseProvider


logger = logging.getLogger(__name__)


type Provider = Any


class ProviderFactory:
    """Resolve and lazily construct provider implementations."""

    def __init__(self) -> None:
        """Initialize the provider registry."""
        logger.info("Initializing ProviderFactory")
        self._registry: dict[str, type[BaseProvider]] = {}
        self._discover_plugins()

    def _discover_plugins(self) -> None:
        import_package_modules(providers, exclude={"provider", "provider_factory", "__init__"})
        for provider_cls in classes_defined_in_package(BaseProvider, "providers."):
            provider_name = str(getattr(provider_cls, "provider_name", "")).strip().lower()
            if not provider_name:
                continue
            self._registry[provider_name] = provider_cls

        logger.info("Loaded Providers: %s", ", ".join(sorted(self._registry)) or "(none)")

    def get_provider(self, provider_name: str) -> Provider:
        """Return a provider instance for the requested provider name."""
        key = provider_name.strip().lower()
        provider_cls = self._registry.get(key)
        if provider_cls is None:
            raise ValueError(f"Unsupported provider: {provider_name}")

        logger.info("Creating provider: %s", key)
        return provider_cls()

    def default_provider(self) -> Provider:
        """Return the default provider instance resolved from configuration."""
        configured_name = getattr(config.settings, "provider", "openai")
        provider_name = str(configured_name).strip().lower() or "openai"
        return self.get_provider(provider_name)

    def supported_providers(self) -> list[str]:
        """Return the list of provider names supported by this factory."""
        return sorted(self._registry.keys())
