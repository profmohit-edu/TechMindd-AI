"""Simple local template renderer."""

from __future__ import annotations

import logging
from pathlib import Path
from string import Formatter
from typing import Any, Dict, Sequence

from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound


LOGGER = logging.getLogger("techmindd.template_engine")


class _SafeFormatter(Formatter):
    """A Formatter that keeps unknown placeholders as-is and records missing keys."""

    def __init__(self) -> None:
        super().__init__()
        self.missing: list[str] = []

    def get_value(
        self,
        key: str | int,
        args: Sequence[Any],
        kwargs: dict[str, Any],
    ) -> Any:
        if isinstance(key, str) and key not in kwargs:
            self.missing.append(key)
            return "{" + key + "}"
        return super().get_value(key, args, kwargs)


class TemplateEngine:
    """Render templates locally using Python format placeholders or Jinja2 files."""

    def __init__(self, templates_dir: str | Path = "templates") -> None:
        self.templates_dir = Path(templates_dir)
        self._jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=StrictUndefined,
        )

    def render(self, template: str, context: Dict[str, Any] | None = None) -> str:
        if context is None:
            context = {}
        if not isinstance(template, str):
            raise TypeError("template must be a string")
        if not isinstance(context, dict):
            raise TypeError("context must be a dictionary")

        safe_context = {k: ("" if v is None else v) for k, v in context.items()}

        if template.endswith(".jinja2"):
            try:
                jinja_template = self._jinja_env.get_template(template)
                return jinja_template.render(**safe_context)
            except TemplateNotFound:
                LOGGER.warning("Template file not found: %s", template)
                return ""

        formatter = _SafeFormatter()
        result = formatter.vformat(template, (), safe_context)
        for key in formatter.missing:
            LOGGER.warning("Missing template placeholder: %s", key)
        return result
