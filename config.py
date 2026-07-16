"""Runtime configuration for TechMindd-AI."""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()
LOGGER = logging.getLogger("techmindd.config")


@dataclass(frozen=True)
class Settings:
    """Runtime configuration loaded from environment variables."""

    provider: str
    openai_api_key: str = ""
    writer_plugin: str = "markdown"
    exporter_plugin: str = "directory"
    retriever_plugin: str = "chroma"
    template_pack: str = "default"
    specialist_agents: tuple[str, ...] = ("research", "script", "seo", "thumbnail", "social")
    director_agent: str = "director"
    openai_model: str = "gpt-4o-mini"
    openai_timeout_seconds: float = 60.0
    openai_temperature: float = 0.2
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    gemini_timeout_seconds: float = 60.0
    gemini_temperature: float = 0.2
    rag_enabled: bool = True
    rag_top_k: int = 5

    @classmethod
    def from_env(cls) -> "Settings":
        provider = os.getenv("PROVIDER", "openai").strip().lower() or "openai"
        if not provider:
            raise ValueError("PROVIDER must be a non-empty provider plugin name")

        writer_plugin = os.getenv("WRITER_PLUGIN", "markdown").strip().lower() or "markdown"
        exporter_plugin = os.getenv("EXPORTER_PLUGIN", "directory").strip().lower() or "directory"
        retriever_plugin = os.getenv("RETRIEVER_PLUGIN", "chroma").strip().lower() or "chroma"
        template_pack = os.getenv("TEMPLATE_PACK", "default").strip().lower() or "default"
        director_agent = os.getenv("DIRECTOR_AGENT", "director").strip().lower() or "director"
        specialist_agents_raw = os.getenv("SPECIALIST_AGENTS", "research,script,seo,thumbnail,social")
        specialist_entries = [entry.strip().lower() for entry in specialist_agents_raw.split(",")]
        if any(not entry for entry in specialist_entries):
            LOGGER.warning("SPECIALIST_AGENTS contains empty entries; they will be ignored")
        specialist_agents = tuple(
            entry for entry in specialist_entries if entry
        )
        if not specialist_agents:
            raise ValueError("SPECIALIST_AGENTS must include at least one agent plugin name")

        openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if provider == "openai" and not openai_api_key:
            raise ValueError(
                "Missing required environment variable OPENAI_API_KEY when PROVIDER=openai. "
                "Set it in your shell or in a .env file."
            )

        openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"

        openai_timeout_raw = os.getenv("OPENAI_TIMEOUT_SECONDS", "60").strip()
        openai_temperature_raw = os.getenv("OPENAI_TEMPERATURE", "0.2").strip()

        gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if provider == "gemini" and not gemini_api_key:
            raise ValueError(
                "Missing required environment variable GEMINI_API_KEY when PROVIDER=gemini. "
                "Set it in your shell or in a .env file."
            )

        gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip() or "gemini-1.5-flash"
        gemini_timeout_raw = os.getenv("GEMINI_TIMEOUT_SECONDS", "60").strip()
        gemini_temperature_raw = os.getenv("GEMINI_TEMPERATURE", "0.2").strip()

        rag_enabled_raw = os.getenv("RAG_ENABLED", "true").strip().lower()
        rag_top_k_raw = os.getenv("RAG_TOP_K", "5").strip()

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

        return cls(
            provider=provider,
            writer_plugin=writer_plugin,
            exporter_plugin=exporter_plugin,
            retriever_plugin=retriever_plugin,
            template_pack=template_pack,
            specialist_agents=specialist_agents,
            director_agent=director_agent,
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
        )


settings = Settings.from_env()
