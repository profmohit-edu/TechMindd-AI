"""Director agent implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from agents.base_agent import BaseAgent
from providers.provider import BaseProvider


class DirectorAgent(BaseAgent):
    """Plans a full package strategy before specialist agents execute."""
    agent_name = "director"

    def __init__(self, provider: BaseProvider) -> None:
        super().__init__(provider)
        self._prompt_path = Path("prompts/director.txt")

    def generate(
        self,
        topic: str,
        director_plan: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Generate a high-level content plan for downstream agents."""
        _ = director_plan
        system_prompt = self._prompt_path.read_text(encoding="utf-8")
        user_prompt = f"Topic: {topic}"
        return self.provider.generate_structured_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "package_name": {"type": "string"},
                    "audience": {"type": "string"},
                    "tone": {"type": "string"},
                    "goal": {"type": "string"},
                    "research_focus": {"type": "string"},
                    "script_focus": {"type": "string"},
                    "seo_focus": {"type": "string"},
                    "thumbnail_focus": {"type": "string"},
                    "social_focus": {"type": "string"},
                },
                "required": [
                    "package_name",
                    "audience",
                    "tone",
                    "goal",
                    "research_focus",
                    "script_focus",
                    "seo_focus",
                    "thumbnail_focus",
                    "social_focus",
                ],
            },
        )
