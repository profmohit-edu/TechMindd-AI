"""Directory exporter plugin."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from exporters.base import BaseExporterPlugin


class DirectoryExporter(BaseExporterPlugin):
    exporter_name = "directory"

    def export(self, *, package_dir: Path, files_written: Iterable[Path]) -> dict:
        written = [str(path) for path in files_written]
        return {
            "exporter": self.exporter_name,
            "output_dir": str(package_dir.resolve()),
            "files_written": written,
            "file_count": len(written),
        }

