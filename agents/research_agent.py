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
        self._prompt_path = Path("prompts/research.txt")

    def generate(
        self,
        topic: str,
        director_plan: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        system_prompt = self._prompt_path.read_text(encoding="utf-8")
        user_prompt = f"Topic: {topic}"
        if director_plan is not None and (research_focus := director_plan.get("research_focus")):
            user_prompt = f"{user_prompt}\nResearch focus: {research_focus}"
        return self.provider.generate_structured_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "audience": {"type": "string"},
                    "summary": {"type": "string"},
                    "insights": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["topic", "audience", "summary", "insights"],
            },
        )
