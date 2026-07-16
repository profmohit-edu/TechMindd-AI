"""Dynamic exporter plugin factory."""

from __future__ import annotations

import logging

import config
import exporters
from exporters.base import BaseExporterPlugin
from plugins.discovery import classes_defined_in_package, import_package_modules


LOGGER = logging.getLogger("techmindd.exporters.factory")


class ExporterPluginFactory:
    """Discover and resolve exporter plugins."""

    def __init__(self) -> None:
        self._registry: dict[str, BaseExporterPlugin] = {}
        self._discover_plugins()

    def _discover_plugins(self) -> None:
        import_package_modules(exporters, exclude={"base", "factory", "__init__"})
        for exporter_cls in classes_defined_in_package(BaseExporterPlugin, "exporters."):
            name = str(getattr(exporter_cls, "exporter_name", "")).strip().lower()
            if not name:
                continue
            self._registry[name] = exporter_cls()
        LOGGER.info("Loaded Exporters: %s", ", ".join(sorted(self._registry)) or "(none)")

    def get_exporter(self, name: str) -> BaseExporterPlugin:
        key = name.strip().lower()
        exporter = self._registry.get(key)
        if exporter is None:
            raise ValueError(f"Unsupported exporter plugin: {name}")
        return exporter

    def default_exporter(self) -> BaseExporterPlugin:
        return self.get_exporter(config.settings.exporter_plugin)

    def supported_exporters(self) -> list[str]:
        return sorted(self._registry)

