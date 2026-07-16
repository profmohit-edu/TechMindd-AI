"""ZIP exporter plugin."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable
from zipfile import ZIP_DEFLATED, ZipFile

from exporters.base import BaseExporterPlugin


class ZipExporter(BaseExporterPlugin):
    exporter_name = "zip"

    def export(self, *, package_dir: Path, files_written: Iterable[Path]) -> dict:
        files = [Path(path) for path in files_written]
        zip_path = package_dir.parent / f"{package_dir.name}.zip"
        with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as archive:
            for path in files:
                archive.write(path, arcname=path.relative_to(package_dir))

        return {
            "exporter": self.exporter_name,
            "output_dir": str(package_dir.resolve()),
            "archive_path": str(zip_path.resolve()),
            "files_written": [str(path) for path in files],
            "file_count": len(files),
        }

