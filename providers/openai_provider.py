"""OpenAI provider for single-shot structured generation."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import requests


class OpenAIProvider:
    """Minimal OpenAI responses API wrapper.

    Guarantees a single network request per generation call.
    """

    def __init__(
        self,
        model: str = "gpt-4.1-mini",
        api_key: Optional[str] = None,
        timeout: int = 120,
    ) -> None:
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.timeout = timeout
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required")

    def generate_structured_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: Dict[str, Any],
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """Perform one OpenAI request and return parsed JSON.

        The API is asked to return JSON matching the provided schema.
        """
        url = "https://api.openai.com/v1/responses"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload: Dict[str, Any] = {
            "model": self.model,
            "temperature": temperature,
            "input": [
                {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "package_plan",
                    "schema": response_schema,
                    "strict": True,
                }
            },
        }

        response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()

        raw_text: Optional[str] = None
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"} and content.get("text"):
                    raw_text = content["text"]
                    break
            if raw_text:
                break

        if raw_text is None:
            raw_text = data.get("output_text")

        if not raw_text:
            raise ValueError("OpenAI response did not include JSON text output")

        try:
            return json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ValueError("Failed to parse OpenAI JSON output") from exc
