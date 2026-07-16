"""Registry for all specialized content agents."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

import config
from agents.base_agent import BaseAgent
from agents.director_agent import DirectorAgent
from agents.research_agent import ResearchAgent
from agents.script_agent import ScriptAgent
from agents.seo_agent import SEOAgent
from agents.thumbnail_agent import ThumbnailAgent
from agents.social_agent import SocialAgent
from providers.openai_provider import OpenAIProvider
from rag.paths import resolve_embeddings_dir
from rag.retriever import Retriever
from rag.vector_store import ChromaVectorStore


LOGGER = logging.getLogger("techmindd.agents.registry")


class AgentRegistry:
    """Centralized registry for initializing and accessing agents."""

    def __init__(self, provider: OpenAIProvider) -> None:
        retriever = self._build_retriever()
        self._agents: Dict[str, BaseAgent] = {
            "director": DirectorAgent(provider),
            "research": ResearchAgent(provider, retriever=retriever),
            "script": ScriptAgent(provider),
            "seo": SEOAgent(provider),
            "thumbnail": ThumbnailAgent(provider),
            "social": SocialAgent(provider),
        }

    def _build_retriever(self) -> Retriever | None:
        if not config.settings.rag_enabled:
            LOGGER.info("RAG disabled by configuration")
            return None

        store_dir = resolve_embeddings_dir()
        if not store_dir.exists():
            LOGGER.info("Knowledge embeddings directory not found; RAG disabled for this run")
            return None

        try:
            store = ChromaVectorStore(persist_directory=store_dir)
            return Retriever(vector_store=store)
        except Exception:
            LOGGER.exception("Failed to initialize retriever; continuing without RAG")
            return None

    def get(self, name: str) -> BaseAgent:
        """Return a registered agent by name."""
        if name not in self._agents:
            raise KeyError(f"Unknown agent: {name}")
        return self._agents[name]

    def all(self) -> Dict[str, BaseAgent]:
        """Return all registered agents keyed by name."""
        return dict(self._agents)

    def names(self) -> List[str]:
        """Return all registered agent names."""
        return list(self._agents.keys())
