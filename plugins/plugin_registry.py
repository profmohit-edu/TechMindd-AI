"""Ordered registry for discovered content plugins."""

from __future__ import annotations

from pathlib import PurePosixPath

from plugins.plugin import BasePlugin


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, BasePlugin] = {}
        self._outputs: set[str] = set()

    def register(self, plugin: BasePlugin) -> None:
        name = plugin.name().strip().lower()
        if not name:
            raise ValueError("plugin name cannot be empty")
        if name in self._plugins:
            raise ValueError(f"duplicate plugin name: {name}")
        output = PurePosixPath(plugin.output_name().replace("\\", "/"))
        if output.is_absolute() or ".." in output.parts or output.suffix != ".md":
            raise ValueError(f"plugin {name} has an unsafe Markdown output name")
        if output.as_posix() in self._outputs:
            raise ValueError(f"plugin {name} duplicates output name: {output}")
        self._plugins[name] = plugin
        self._outputs.add(output.as_posix())

    def get(self, name: str) -> BasePlugin:
        try:
            return self._plugins[name]
        except KeyError as exc:
            raise KeyError(f"Unknown plugin: {name}") from exc

    def all(self) -> list[BasePlugin]:
        return sorted(self._plugins.values(), key=lambda plugin: (plugin.order(), plugin.name()))

    def names(self) -> list[str]:
        return [plugin.name() for plugin in self.all()]
