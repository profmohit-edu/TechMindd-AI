"""Script agent implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from agents.base_agent import BaseAgent
from providers.provider import BaseProvider


class ScriptAgent(BaseAgent):
    """Generates structured script payloads."""
    agent_name = "script"

    def __init__(self, provider: BaseProvider) -> None:
        super().__init__(provider)
        self._prompt_path = Path("prompts/script.txt")

    def generate(
        self,
        topic: str,
        director_plan: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        system_prompt = self._prompt_path.read_text(encoding="utf-8")
        user_prompt = f"Topic: {topic}"
        if director_plan is not None and (script_focus := director_plan.get("script_focus")):
            user_prompt = f"{user_prompt}\nScript focus: {script_focus}"
        return self.provider.generate_structured_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "hook": {"type": "string"},
                    "sections": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["title", "hook", "sections"],
            },
        )
