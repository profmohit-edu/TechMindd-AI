"""Simple local template renderer."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from string import Formatter
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound

from core.template_pack_registry import TemplatePackRegistry


LOGGER = logging.getLogger("techmindd.template_engine")


class _SafeFormatter(Formatter):
    def get_value(self, key: object, args: Any, kwargs: Dict[str, Any]) -> Any:
        if isinstance(key, str) and key not in kwargs:
            LOGGER.warning("Missing template placeholder: %s", key)
            return "{" + key + "}"
        return Formatter.get_value(self, key, args, kwargs)


class TemplateEngine:
    """Render templates locally using Python format placeholders or Jinja2 files."""

    def __init__(self, templates_dir: str | Path = "templates", template_pack: str | None = None) -> None:
        self._template_pack_registry = TemplatePackRegistry(templates_root=templates_dir)
        selected_pack = template_pack or os.getenv("TEMPLATE_PACK", "default")
        self.templates_dir = self._template_pack_registry.get_pack_path(selected_pack)
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
        return formatter.vformat(template, (), safe_context)
