"""Package writer that renders and writes all planned files."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List

from core.template_engine import TemplateEngine
from core.writer import Writer


class PackageWriter:
    """Render templates and persist output files to disk."""

    def __init__(self, template_engine: TemplateEngine, writer: Writer) -> None:
        self.template_engine = template_engine
        self.writer = writer

    def write_package(
        self,
        files: Iterable[Dict[str, Any]],
        base_path: str | Path = ".",
    ) -> List[Path]:
        base = Path(base_path)
        rendered: list[tuple[str, str]] = []

        for file_spec in files:
            path = str(file_spec.get("path", "")).strip()
            if not path:
                continue

            content = str(file_spec.get("content", ""))
            is_template = bool(file_spec.get("template", False))
            context = file_spec.get("context") or {}

            if is_template:
                processor = str(context.get("processor", "")).strip()
                configured_template = str(context.get("template", "")).strip()
                template_name = configured_template or (f"{processor}.jinja2" if processor else "")
                if template_name:
                    content = self.template_engine.render(template_name, context)

            rendered.append((str((base / path).as_posix()), content))

        return [self.writer.write(path, content) for path, content in rendered]
