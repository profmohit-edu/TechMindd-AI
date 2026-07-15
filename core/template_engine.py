"""Simple local template renderer."""

from __future__ import annotations

from typing import Any, Dict


class TemplateEngine:
    """Render templates locally using Python format placeholders."""

    def render(self, template: str, context: Dict[str, Any] | None = None) -> str:
        if context is None:
            context = {}
        if not isinstance(template, str):
            raise TypeError("template must be a string")
        if not isinstance(context, dict):
            raise TypeError("context must be a dictionary")

        safe_context = {k: ("" if v is None else v) for k, v in context.items()}
        return template.format(**safe_context)
