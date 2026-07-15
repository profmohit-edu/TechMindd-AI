"""Registry for all specialized content agents."""

from __future__ import annotations

from typing import Dict, List

from agents.base_agent import BaseAgent
from agents.research_agent import ResearchAgent
from agents.script_agent import ScriptAgent
from agents.seo_agent import SEOAgent
from agents.thumbnail_agent import ThumbnailAgent
from agents.social_agent import SocialAgent
from providers.openai_provider import OpenAIProvider


class AgentRegistry:
    """Centralized registry for initializing and accessing agents."""

    def __init__(self, provider: OpenAIProvider) -> None:
        self._agents: Dict[str, BaseAgent] = {
            "research": ResearchAgent(provider),
            "script": ScriptAgent(provider),
            "seo": SEOAgent(provider),
            "thumbnail": ThumbnailAgent(provider),
            "social": SocialAgent(provider),
        }

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
