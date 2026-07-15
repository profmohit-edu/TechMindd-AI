"""Application configuration for TechMindd-AI."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Runtime configuration loaded from environment variables."""

    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_timeout_seconds: float = 60.0
    openai_temperature: float = 0.2

    @classmethod
    def from_env(cls) -> "Settings":
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ValueError(
                "Missing required environment variable OPENAI_API_KEY. "
                "Set it in your shell or in a .env file."
            )

        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"

        timeout_raw = os.getenv("OPENAI_TIMEOUT_SECONDS", "60").strip()
        temperature_raw = os.getenv("OPENAI_TEMPERATURE", "0.2").strip()

        try:
            timeout_seconds = float(timeout_raw)
        except ValueError as exc:
            raise ValueError("OPENAI_TIMEOUT_SECONDS must be a number") from exc

        try:
            temperature = float(temperature_raw)
        except ValueError as exc:
            raise ValueError("OPENAI_TEMPERATURE must be a number") from exc

        if timeout_seconds <= 0:
            raise ValueError("OPENAI_TIMEOUT_SECONDS must be greater than 0")

        if not 0 <= temperature <= 2:
            raise ValueError("OPENAI_TEMPERATURE must be between 0 and 2")

        return cls(
            openai_api_key=api_key,
            openai_model=model,
            openai_timeout_seconds=timeout_seconds,
            openai_temperature=temperature,
        )


settings = Settings.from_env()
