"""Simple local template renderer."""

from __future__ import annotations

import logging
from collections import UserDict
from string import Formatter
from typing import Any, Dict


LOGGER = logging.getLogger("techmindd.template_engine")


class _SafeFormatDict(UserDict):
    """Mapping that preserves missing placeholders and logs warnings."""

    def __missing__(self, key: str) -> str:
        LOGGER.warning("Missing template placeholder: %s", key)
        return "{" + key + "}"


class TemplateEngine:
    """Render templates locally using Python format placeholders."""

    def render(self, template: str, context: Dict[str, Any] | None = None) -> str:
        if context is None:
            context = {}
        if not isinstance(template, str):
            raise TypeError("template must be a string")
        if not isinstance(context, dict):
            raise TypeError("context must be a dictionary")

        safe_context = _SafeFormatDict(
            {k: ("" if v is None else v) for k, v in context.items()}
        )

        formatter = Formatter()
        return formatter.vformat(template, (), safe_context)
