"""Filesystem discovery for content plugins."""

from __future__ import annotations

import importlib
import inspect
import pkgutil

import plugins
from plugins.plugin import BasePlugin
from plugins.plugin_registry import PluginRegistry


class PluginManager:
    """Discover concrete BasePlugin classes from the plugins package."""

    def discover(self) -> PluginRegistry:
        registry = PluginRegistry()
        for module_info in sorted(pkgutil.iter_modules(plugins.__path__), key=lambda item: item.name):
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
            for plugin_class in classes:
                registry.register(plugin_class())
        return registry
