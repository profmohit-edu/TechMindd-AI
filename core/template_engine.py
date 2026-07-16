"""Simple local template renderer."""

from __future__ import annotations

import logging
from pathlib import Path
from string import Formatter
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound, Undefined


LOGGER = logging.getLogger("techmindd.template_engine")

# Maps document kind → Jinja2 template filename for render_document()
_DOCUMENT_TEMPLATES: Dict[str, str] = {
    "research": "research.md.j2",
    "script": "script.md.j2",
    "seo": "seo.md.j2",
    "thumbnail": "thumbnail.md.j2",
    "social": "social.md.j2",
}


class _SafeFormatter(Formatter):
    """Formatter that logs a warning and keeps the placeholder for missing keys."""

    def get_value(self, key: int | str, args: Any, kwargs: Any) -> Any:
        if isinstance(key, int):
            return args[key]
        try:
            return kwargs[key]
        except KeyError:
            LOGGER.warning("Missing template placeholder: %s", key)
            return "{" + str(key) + "}"


class TemplateEngine:
    """Render templates locally using Python format placeholders or Jinja2 files."""

    def __init__(self, templates_dir: str | Path = "templates") -> None:
        self.templates_dir = Path(templates_dir)
        # Strict environment for legacy .jinja2 templates.
        self._jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=StrictUndefined,
        )
        # Lenient environment for .md.j2 document templates: missing fields render
        # as empty string rather than raising an error.
        self._md_jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=Undefined,
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

        if template.endswith(".md.j2"):
            try:
                jinja_template = self._md_jinja_env.get_template(template)
                return jinja_template.render(**safe_context)
            except TemplateNotFound:
                LOGGER.warning("Template file not found: %s", template)
                return ""

        return _SafeFormatter().vformat(template, (), safe_context)

    def render_document(self, kind: str, data: Dict[str, Any] | None = None) -> str:
        """Render a named document kind (e.g. 'research') using its .md.j2 template.

        Args:
            kind: One of 'research', 'script', 'seo', 'thumbnail', 'social'.
            data: Structured JSON payload returned by the corresponding agent.

        Returns:
            Rendered Markdown string.

        Raises:
            ValueError: If *kind* is not a recognised document type.
        """
        template_name = _DOCUMENT_TEMPLATES.get(kind)
        if template_name is None:
            raise ValueError(
                f"Unknown document kind: {kind!r}. "
                f"Expected one of: {sorted(_DOCUMENT_TEMPLATES)}"
            )
        safe_data = {k: ("" if v is None else v) for k, v in (data or {}).items()}
        return self.render(template_name, safe_data)
