"""Base writer plugin abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseWriterPlugin(ABC):
    """Transform rendered template content into final output format."""

    writer_name: str = ""
    file_extension: str = ".md"

    @abstractmethod
    def transform(self, rendered_content: str, context: Dict[str, Any]) -> str:
        """Return final content for output file."""
        raise NotImplementedError

