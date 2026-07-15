"""Research agent implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from agents.base_agent import BaseAgent
from providers.openai_provider import OpenAIProvider


class ResearchAgent(BaseAgent):
    """Generates structured research payloads."""

    def __init__(self, provider: OpenAIProvider) -> None:
        super().__init__(provider)
        self._system_prompt = Path("prompts/research_system.txt").read_text(encoding="utf-8")

    def generate(self, topic: str) -> Dict[str, Any]:
        user_prompt = f"Generate a structured research payload for topic: {topic}."
        return self.provider.generate_structured_json(
            system_prompt=self._system_prompt,
            user_prompt=user_prompt,
            response_schema={"type": "object"},
        )
