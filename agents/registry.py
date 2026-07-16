"""Registry for all specialized content agents."""

from __future__ import annotations

import logging
import inspect
from typing import Dict, List

import agents
from agents.base_agent import BaseAgent
from plugins.discovery import classes_defined_in_package, import_package_modules
from providers.provider import BaseProvider
from rag.retriever import Retriever
from rag.retriever_factory import RetrieverFactory


LOGGER = logging.getLogger("techmindd.agents.registry")


class AgentRegistry:
    """Centralized registry for initializing and accessing agents."""

    def __init__(self, provider: BaseProvider) -> None:
        retriever = RetrieverFactory().default_retriever()
        self._agents: Dict[str, BaseAgent] = {}
        self._discover_agents(provider, retriever)

    def _discover_agents(self, provider: BaseProvider, retriever: Retriever | None) -> None:
        import_package_modules(agents, exclude={"base_agent", "registry", "__init__"})
        for agent_cls in classes_defined_in_package(BaseAgent, "agents."):
            name = str(getattr(agent_cls, "agent_name", "")).strip().lower()
            if not name:
                class_name = agent_cls.__name__.removesuffix("Agent")
                name = class_name.lower()
                LOGGER.warning("Agent %s missing explicit agent_name; using derived name '%s'", agent_cls.__name__, name)

            kwargs: dict[str, object] = {}
            signature = inspect.signature(agent_cls.__init__)
            if "retriever" in signature.parameters:
                kwargs["retriever"] = retriever

            self._agents[name] = agent_cls(provider, **kwargs)

        LOGGER.info("Loaded Agents: %s", ", ".join(sorted(self._agents)) or "(none)")

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
