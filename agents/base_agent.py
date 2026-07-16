"""Base agent abstraction for structured payload generation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from providers.provider import BaseProvider


class BaseAgent(ABC):
    """Abstract base class for all specialized agents."""

    agent_name: str = ""

    def __init__(self, provider: BaseProvider) -> None:
        self.provider = provider

    @abstractmethod
    def generate(
        self,
        topic: str,
        director_plan: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Generate a structured payload for a given topic."""
