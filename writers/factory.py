"""Dynamic writer plugin factory."""

from __future__ import annotations

import logging

import config
import writers
from plugins.discovery import classes_defined_in_package, import_package_modules
from writers.base import BaseWriterPlugin


LOGGER = logging.getLogger("techmindd.writers.factory")


class WriterPluginFactory:
    """Discover and instantiate writer plugins."""

    def __init__(self) -> None:
        self._registry: dict[str, BaseWriterPlugin] = {}
        self._discover_plugins()

    def _discover_plugins(self) -> None:
        import_package_modules(writers, exclude={"base", "factory", "__init__"})
        for writer_cls in classes_defined_in_package(BaseWriterPlugin, "writers."):
            name = str(getattr(writer_cls, "writer_name", "")).strip().lower()
            if not name:
                continue
            self._registry[name] = writer_cls()
        LOGGER.info("Loaded Writers: %s", ", ".join(sorted(self._registry)) or "(none)")

    def get_writer(self, name: str) -> BaseWriterPlugin:
        key = name.strip().lower()
        writer = self._registry.get(key)
        if writer is None:
            raise ValueError(f"Unsupported writer plugin: {name}")
        return writer

    def default_writer(self) -> BaseWriterPlugin:
        return self.get_writer(config.settings.writer_plugin)

    def supported_writers(self) -> list[str]:
        return sorted(self._registry)

