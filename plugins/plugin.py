"""Base plugin contract and generic plugin-backed agent."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from agents.base_agent import BaseAgent


class PluginAgent(BaseAgent):
    """Generate a plugin payload from its prompt and schema."""

    def __init__(self, provider: Any, plugin: "BasePlugin") -> None:
        super().__init__(provider)
        self._plugin = plugin

    def generate(
        self,
        topic: str,
        director_plan: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        prompt = Path(self._plugin.prompt_template()).read_text(encoding="utf-8")
        user_prompt = f"Topic: {topic}"
        if director_plan is not None:
            focus = director_plan.get(f"{self._plugin.name()}_focus")
            if focus:
                user_prompt = f"{user_prompt}\nContent focus: {focus}"
        return self.provider.generate_structured_json(
            system_prompt=prompt,
            user_prompt=user_prompt,
            response_schema=self._plugin.schema(),
        )


class BasePlugin(ABC):
    """Complete contract for a dynamically discovered content generator."""

    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def output_name(self) -> str: ...

    @abstractmethod
    def prompt_template(self) -> str: ...

    @abstractmethod
    def schema(self) -> dict[str, Any]: ...

    @abstractmethod
    def processor(self) -> Any: ...

    @abstractmethod
    def validator(self) -> Any: ...

    @abstractmethod
    def scorer(self) -> Any: ...

    @abstractmethod
    def reflector(self) -> Any: ...

    @abstractmethod
    def template(self) -> str: ...

    def order(self) -> int:
        return 100

    def create_agent(self, provider: Any, retriever: Any | None = None) -> BaseAgent:
        _ = retriever
        return PluginAgent(provider, self)
