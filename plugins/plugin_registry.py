"""Ordered registry for discovered content plugins."""

from __future__ import annotations

from plugins.plugin import BasePlugin


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, BasePlugin] = {}

    def register(self, plugin: BasePlugin) -> None:
        name = plugin.name().strip().lower()
        if not name:
            raise ValueError("plugin name cannot be empty")
        if name in self._plugins:
            raise ValueError(f"duplicate plugin name: {name}")
        self._plugins[name] = plugin

    def get(self, name: str) -> BasePlugin:
        try:
            return self._plugins[name]
        except KeyError as exc:
            raise KeyError(f"Unknown plugin: {name}") from exc

    def all(self) -> list[BasePlugin]:
        return sorted(self._plugins.values(), key=lambda plugin: (plugin.order(), plugin.name()))

    def names(self) -> list[str]:
        return [plugin.name() for plugin in self.all()]
