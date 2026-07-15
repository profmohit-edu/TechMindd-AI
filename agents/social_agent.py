"""Social agent implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from agents.base_agent import BaseAgent
from providers.openai_provider import OpenAIProvider


class SocialAgent(BaseAgent):
    """Generates structured social payloads."""

    def __init__(self, provider: OpenAIProvider) -> None:
        super().__init__(provider)
        self._prompt_path = Path("prompts/social.txt")

    def generate(self, topic: str) -> Dict[str, Any]:
        system_prompt = self._prompt_path.read_text(encoding="utf-8")
        user_prompt = f"Topic: {topic}"
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
