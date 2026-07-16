"""Simple local template renderer."""

from __future__ import annotations

import logging
from pathlib import Path
from string import Formatter
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound


LOGGER = logging.getLogger("techmindd.template_engine")


class _PlaceholderContext(dict[str, Any]):
    def __missing__(self, key: str) -> str:
        LOGGER.warning("Missing template placeholder: %s", key)
        return "{" + key + "}"


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

        safe_context = _PlaceholderContext(
            {k: ("" if v is None else v) for k, v in context.items()}
        )

        if template.endswith(".jinja2"):
            try:
                jinja_template = self._jinja_env.get_template(template)
                return jinja_template.render(**safe_context)
            except TemplateNotFound:
                LOGGER.warning("Template file not found: %s", template)
                return ""

        formatter = Formatter()
        return formatter.vformat(template, (), safe_context)
