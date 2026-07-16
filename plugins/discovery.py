"""Dynamic plugin discovery primitives."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from types import ModuleType
from typing import TypeVar


T = TypeVar("T")


def import_package_modules(package: ModuleType, *, exclude: set[str] | None = None) -> None:
    excluded = exclude or set()
    for module_info in pkgutil.iter_modules(package.__path__, f"{package.__name__}."):
        module_name = module_info.name.rsplit(".", 1)[-1]
        if module_name in excluded:
            continue
        importlib.import_module(module_info.name)


def iter_subclasses(base_class: type[T]) -> list[type[T]]:
    discovered: list[type[T]] = []
    stack = list(base_class.__subclasses__())
    while stack:
        cls = stack.pop()
        discovered.append(cls)
        stack.extend(cls.__subclasses__())
    return discovered


def classes_defined_in_package(base_class: type[T], package_prefix: str) -> list[type[T]]:
    matches: list[type[T]] = []
    for cls in iter_subclasses(base_class):
        if cls.__module__.startswith(package_prefix):
            matches.append(cls)
    return matches


def construct_noarg_plugins(classes: list[type[T]]) -> dict[str, T]:
    plugins: dict[str, T] = {}
    for cls in classes:
        signature = inspect.signature(cls.__init__)
        if len(signature.parameters) > 1:
            continue
        instance = cls()
        plugin_name = getattr(instance, "plugin_name", "") or getattr(instance, "name", "")
        if plugin_name:
            plugins[str(plugin_name).strip().lower()] = instance
    return plugins

