"""Production content plugin architecture."""

from plugins.plugin import BasePlugin
from plugins.plugin_manager import PluginManager
from plugins.plugin_registry import PluginRegistry

__all__ = ["BasePlugin", "PluginManager", "PluginRegistry"]
