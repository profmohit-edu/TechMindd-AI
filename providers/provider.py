"""Base provider interface for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseProvider(ABC):
    """Abstract interface for model providers used by the pipeline."""

    @abstractmethod
    def generate_structured_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Return a structured JSON object that satisfies ``response_schema``."""
        raise NotImplementedError
