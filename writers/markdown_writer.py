"""Markdown writer plugin."""

from __future__ import annotations

from typing import Any, Dict

from writers.base import BaseWriterPlugin


class MarkdownWriter(BaseWriterPlugin):
    writer_name = "markdown"
    file_extension = ".md"

    def transform(self, rendered_content: str, _context: Dict[str, Any]) -> str:
        # Markdown output is the rendered template as-is.
        return rendered_content
