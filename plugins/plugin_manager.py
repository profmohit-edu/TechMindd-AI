"""Filesystem discovery for content plugins."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from functools import lru_cache
from pathlib import Path

from plugins.plugin import BasePlugin
from plugins.plugin_registry import PluginRegistry


class PluginManager:
    """Discover concrete BasePlugin classes from the plugins package."""

    def discover(self) -> PluginRegistry:
        registry = PluginRegistry()
        for plugin_class in self._plugin_classes():
            registry.register(plugin_class())
        return registry

    @staticmethod
    @lru_cache(maxsize=1)
    def _plugin_classes() -> tuple[type[BasePlugin], ...]:
        package_dir = Path(__file__).resolve().parent
        discovered: list[type[BasePlugin]] = []
        for module_info in sorted(
            pkgutil.iter_modules([str(package_dir)]), key=lambda item: item.name
        ):
            if not module_info.name.endswith("_plugin"):
                continue
            module = importlib.import_module(f"plugins.{module_info.name}")
            classes = [
                candidate
                for _, candidate in inspect.getmembers(module, inspect.isclass)
                if candidate.__module__ == module.__name__
                and issubclass(candidate, BasePlugin)
                and candidate is not BasePlugin
                and not inspect.isabstract(candidate)
            ]
            discovered.extend(classes)
        return tuple(discovered)
