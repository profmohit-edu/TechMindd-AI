"""Base exporter plugin abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable


class BaseExporterPlugin(ABC):
    """Export generated files using a plugin strategy."""

    exporter_name: str = ""

    @abstractmethod
    def export(self, *, package_dir: Path, files_written: Iterable[Path]) -> dict:
        """Export generated files and return result metadata."""
        raise NotImplementedError

