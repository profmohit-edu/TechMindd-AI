"""Runtime configuration for TechMindd-AI."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Runtime configuration loaded from environment variables."""

    provider: str
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_timeout_seconds: float = 60.0
    openai_temperature: float = 0.2
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    gemini_timeout_seconds: float = 60.0
    gemini_temperature: float = 0.2
    rag_enabled: bool = True
    rag_top_k: int = 5
    provider_priority: tuple[str, ...] = ("openai", "gemini")
    provider_max_retries: int = 1
    provider_request_timeout_seconds: float = 60.0
    run_token_budget: int | None = None
    run_cost_budget: float | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        provider = os.getenv("PROVIDER", "auto").strip().lower() or "auto"
        if provider not in {"auto", "openai", "gemini"}:
            raise ValueError("PROVIDER must be one of: auto, openai, gemini")

        openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()

        openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"

        openai_timeout_raw = os.getenv("OPENAI_TIMEOUT_SECONDS", "60").strip()
        openai_temperature_raw = os.getenv("OPENAI_TEMPERATURE", "0.2").strip()

        gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip() or "gemini-1.5-flash"
        gemini_timeout_raw = os.getenv("GEMINI_TIMEOUT_SECONDS", "60").strip()
        gemini_temperature_raw = os.getenv("GEMINI_TEMPERATURE", "0.2").strip()

        rag_enabled_raw = os.getenv("RAG_ENABLED", "true").strip().lower()
        rag_top_k_raw = os.getenv("RAG_TOP_K", "5").strip()
        default_priority = "openai,gemini" if provider == "auto" else f"{provider},openai,gemini"
        priority_raw = os.getenv("PROVIDER_PRIORITY", "").strip() or default_priority
        provider_priority = tuple(
            dict.fromkeys(item.strip().lower() for item in priority_raw.split(",") if item.strip())
        )
        provider_max_retries_raw = os.getenv("PROVIDER_MAX_RETRIES", "1").strip()
        provider_timeout_raw = os.getenv("PROVIDER_REQUEST_TIMEOUT_SECONDS", "60").strip()
        run_token_budget_raw = os.getenv("RUN_TOKEN_BUDGET", "").strip()
        run_cost_budget_raw = os.getenv("RUN_COST_BUDGET", "").strip()

        try:
            openai_timeout_seconds = float(openai_timeout_raw)
        except ValueError as exc:
            raise ValueError("OPENAI_TIMEOUT_SECONDS must be a number") from exc

        try:
            openai_temperature = float(openai_temperature_raw)
        except ValueError as exc:
            raise ValueError("OPENAI_TEMPERATURE must be a number") from exc

        try:
            gemini_timeout_seconds = float(gemini_timeout_raw)
        except ValueError as exc:
            raise ValueError("GEMINI_TIMEOUT_SECONDS must be a number") from exc

        try:
            gemini_temperature = float(gemini_temperature_raw)
        except ValueError as exc:
            raise ValueError("GEMINI_TEMPERATURE must be a number") from exc

        if rag_enabled_raw in {"1", "true", "yes", "on"}:
            rag_enabled = True
        elif rag_enabled_raw in {"0", "false", "no", "off"}:
            rag_enabled = False
        else:
            raise ValueError("RAG_ENABLED must be a boolean value (true/false)")

        try:
            rag_top_k = int(rag_top_k_raw)
        except ValueError as exc:
            raise ValueError("RAG_TOP_K must be an integer") from exc

        try:
            provider_max_retries = int(provider_max_retries_raw)
        except ValueError as exc:
            raise ValueError("PROVIDER_MAX_RETRIES must be an integer") from exc

        try:
            provider_request_timeout_seconds = float(provider_timeout_raw)
        except ValueError as exc:
            raise ValueError("PROVIDER_REQUEST_TIMEOUT_SECONDS must be a number") from exc

        try:
            run_token_budget = int(run_token_budget_raw) if run_token_budget_raw else None
        except ValueError as exc:
            raise ValueError("RUN_TOKEN_BUDGET must be an integer") from exc

        try:
            run_cost_budget = float(run_cost_budget_raw) if run_cost_budget_raw else None
        except ValueError as exc:
            raise ValueError("RUN_COST_BUDGET must be a number") from exc

        if openai_timeout_seconds <= 0:
            raise ValueError("OPENAI_TIMEOUT_SECONDS must be greater than 0")

        if not 0 <= openai_temperature <= 2:
            raise ValueError("OPENAI_TEMPERATURE must be between 0 and 2")

        if gemini_timeout_seconds <= 0:
            raise ValueError("GEMINI_TIMEOUT_SECONDS must be greater than 0")

        if not 0 <= gemini_temperature <= 2:
            raise ValueError("GEMINI_TEMPERATURE must be between 0 and 2")

        if rag_top_k <= 0:
            raise ValueError("RAG_TOP_K must be greater than 0")
        if not provider_priority:
            raise ValueError("PROVIDER_PRIORITY must contain at least one provider")
        if provider_max_retries < 0:
            raise ValueError("PROVIDER_MAX_RETRIES cannot be negative")
        if provider_request_timeout_seconds <= 0:
            raise ValueError("PROVIDER_REQUEST_TIMEOUT_SECONDS must be greater than 0")
        if run_token_budget is not None and run_token_budget <= 0:
            raise ValueError("RUN_TOKEN_BUDGET must be greater than 0")
        if run_cost_budget is not None and run_cost_budget <= 0:
            raise ValueError("RUN_COST_BUDGET must be greater than 0")

        return cls(
            provider=provider,
            openai_api_key=openai_api_key,
            openai_model=openai_model,
            openai_timeout_seconds=openai_timeout_seconds,
            openai_temperature=openai_temperature,
            gemini_api_key=gemini_api_key,
            gemini_model=gemini_model,
            gemini_timeout_seconds=gemini_timeout_seconds,
            gemini_temperature=gemini_temperature,
            rag_enabled=rag_enabled,
            rag_top_k=rag_top_k,
            provider_priority=provider_priority,
            provider_max_retries=provider_max_retries,
            provider_request_timeout_seconds=provider_request_timeout_seconds,
            run_token_budget=run_token_budget,
            run_cost_budget=run_cost_budget,
        )


settings = Settings.from_env()
