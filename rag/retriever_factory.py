"""Dynamic retriever plugin factory."""

from __future__ import annotations

import logging

import config
import rag.plugins
from plugins.discovery import classes_defined_in_package, import_package_modules
from rag.plugins.base import BaseRetrieverPlugin
from rag.retriever import Retriever


LOGGER = logging.getLogger("techmindd.retrievers.factory")


class RetrieverFactory:
    """Load retriever plugins dynamically and resolve configured plugin."""

    def __init__(self) -> None:
        self._registry: dict[str, type[BaseRetrieverPlugin]] = {}
        self._discover_plugins()

    def _discover_plugins(self) -> None:
        import_package_modules(rag.plugins, exclude={"base", "__init__"})
        for plugin_cls in classes_defined_in_package(BaseRetrieverPlugin, "rag.plugins."):
            plugin_name = str(getattr(plugin_cls, "retriever_name", "")).strip().lower()
            if not plugin_name:
                continue
            self._registry[plugin_name] = plugin_cls
        LOGGER.info("Loaded Retrievers: %s", ", ".join(sorted(self._registry)) or "(none)")

    def get_retriever(self, name: str) -> Retriever | None:
        plugin_cls = self._registry.get(name.strip().lower())
        if plugin_cls is None:
            raise ValueError(f"Unsupported retriever plugin: {name}")
        return plugin_cls().build()

    def default_retriever(self) -> Retriever | None:
        return self.get_retriever(config.settings.retriever_plugin)

    def supported_retrievers(self) -> list[str]:
        return sorted(self._registry)

