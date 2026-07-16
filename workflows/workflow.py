"""Typed workflow configuration model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Workflow:
    name: str
    description: str
    provider: str
    plugins: tuple[str, ...]
    validation: bool
    quality: bool
    reflection: bool
    parallel: bool
    output: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Workflow":
        if not isinstance(payload, dict):
            raise TypeError("workflow YAML must contain an object")
        name = cls._required_string(payload, "name")
        description = str(payload.get("description", "")).strip()
        provider = str(payload.get("provider", "auto")).strip().lower() or "auto"
        raw_plugins = payload.get("plugins")
        if not isinstance(raw_plugins, list) or not raw_plugins:
            raise ValueError("workflow plugins must be a non-empty list")
        plugins = tuple(str(item).strip().lower() for item in raw_plugins if str(item).strip())
        if len(plugins) != len(raw_plugins) or len(set(plugins)) != len(plugins):
            raise ValueError("workflow plugins must be unique non-empty names")

        validation = cls._boolean(payload, "validation", True)
        quality = cls._boolean(payload, "quality", True)
        reflection = cls._boolean(payload, "reflection", True)
        parallel = cls._boolean(payload, "parallel", True)
        if reflection and not quality:
            raise ValueError("workflow reflection requires quality scoring")
        output = str(payload.get("output", "output")).strip() or "output"
        return cls(
            name=name,
            description=description,
            provider=provider,
            plugins=plugins,
            validation=validation,
            quality=quality,
            reflection=reflection,
            parallel=parallel,
            output=output,
        )

    @classmethod
    def implicit(cls, plugins: list[str], output: str = "output") -> "Workflow":
        return cls(
            "default",
            "Backward-compatible default workflow",
            "auto",
            tuple(plugins),
            True,
            True,
            True,
            True,
            output,
        )

    @staticmethod
    def _required_string(payload: dict[str, Any], key: str) -> str:
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"workflow {key} must be a non-empty string")
        return value.strip()

    @staticmethod
    def _boolean(payload: dict[str, Any], key: str, default: bool) -> bool:
        value = payload.get(key, default)
        if not isinstance(value, bool):
            raise ValueError(f"workflow {key} must be a boolean")
        return value
