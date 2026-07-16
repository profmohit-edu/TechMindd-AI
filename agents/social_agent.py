"""Social agent implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from agents.base_agent import BaseAgent


class SocialAgent(BaseAgent):
    """Generates structured social payloads."""

    def __init__(self, provider: Any) -> None:
        super().__init__(provider)
        self._prompt_path = Path("prompts/social.txt")

    def generate(
        self,
        topic: str,
        director_plan: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        system_prompt = self._prompt_path.read_text(encoding="utf-8")
        user_prompt = f"Topic: {topic}"
        if director_plan is not None and (social_focus := director_plan.get("social_focus")):
            user_prompt = f"{user_prompt}\nSocial focus: {social_focus}"
        return self.provider.generate_structured_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema={
                "type": "object",
                "properties": {
                    "caption": {"type": "string"},
                    "hashtags": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["caption", "hashtags"],
            },
        )
