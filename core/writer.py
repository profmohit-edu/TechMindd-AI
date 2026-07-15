"""Filesystem writer for generated output files."""

from __future__ import annotations

from pathlib import Path


class Writer:
    """Write output files while preserving folder structure."""

    def __init__(self, base_path: str | Path = ".") -> None:
        self.base_path = Path(base_path)

    def write(self, relative_path: str, content: str) -> Path:
        destination = self.base_path / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
        return destination
