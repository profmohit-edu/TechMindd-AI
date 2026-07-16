"""Package writer that renders and writes all planned files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List

from core.template_engine import TemplateEngine
from core.writer import Writer
from writers.base import BaseWriterPlugin


LOGGER = logging.getLogger("techmindd.package_writer")


class PackageWriter:
    """Render templates and persist output files to disk."""

    def __init__(
        self,
        template_engine: TemplateEngine,
        writer: Writer,
        writer_plugin: BaseWriterPlugin,
    ) -> None:
        self.template_engine = template_engine
        self.writer = writer
        self.writer_plugin = writer_plugin

    def write_package(
        self,
        files: Iterable[Dict[str, Any]],
        base_path: str | Path = ".",
    ) -> List[Path]:
        written: List[Path] = []
        base = Path(base_path)

        for file_spec in files:
            path = str(file_spec.get("path", "")).strip()
            if not path:
                continue

            content = str(file_spec.get("content", ""))
            is_template = bool(file_spec.get("template", False))
            context = file_spec.get("context") or {}

            template_name = str(file_spec.get("template_name", "")).strip()
            if is_template:
                processor = str(context.get("processor", "")).strip()
                resolved_template = template_name or (f"{processor}.jinja2" if processor else "")
                if resolved_template:
                    content = self.template_engine.render(resolved_template, context)

            transformed = self.writer_plugin.transform(content, context)

            relative_path = Path(path)
            if relative_path.suffix != self.writer_plugin.file_extension:
                if relative_path.suffix:
                    LOGGER.warning(
                        "Replacing file suffix '%s' with writer suffix '%s' for %s",
                        relative_path.suffix,
                        self.writer_plugin.file_extension,
                        str(relative_path),
                    )
                relative_path = relative_path.with_suffix(self.writer_plugin.file_extension)

            full_relative = str((base / relative_path).as_posix())
            written.append(self.writer.write(full_relative, transformed))

        return written
