"""HTML writer plugin."""

from __future__ import annotations

from html import escape
from typing import Any, Dict

from writers.base import BaseWriterPlugin


class HTMLWriter(BaseWriterPlugin):
    writer_name = "html"
    file_extension = ".html"

    def transform(self, rendered_content: str, _context: Dict[str, Any]) -> str:
        safe = escape(rendered_content)
        return f"<html><body><pre>{safe}</pre></body></html>\n"
