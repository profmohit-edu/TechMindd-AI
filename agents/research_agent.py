"""Research agent implementation."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, Sequence

import config
from agents.base_agent import BaseAgent
from providers.openai_provider import OpenAIProvider
from rag.retriever import RetrievedChunk, Retriever


LOGGER = logging.getLogger("techmindd.agents.research")


class ResearchAgent(BaseAgent):
    """Generates structured research payloads."""

    def __init__(
        self,
        provider: OpenAIProvider,
        retriever: Retriever | None = None,
    ) -> None:
        super().__init__(provider)
        self._prompt_path = Path("prompts/research.txt")
        self._retriever = retriever

    def _build_context(self, topic: str) -> str:
        if not config.settings.rag_enabled:
            LOGGER.info("RAG disabled via configuration")
            return ""

        if self._retriever is None:
            LOGGER.info("Retriever unavailable; proceeding without RAG context")
            return ""

        started = time.perf_counter()
        retrieved_chunks: list[RetrievedChunk] = self._retriever.retrieve(
            query=topic,
            top_k=config.settings.rag_top_k,
        )
        elapsed = time.perf_counter() - started

        if not retrieved_chunks:
            LOGGER.info("No relevant chunks retrieved in %.3fs", elapsed)
            return ""

        sources: list[str] = [chunk.metadata.source for chunk in retrieved_chunks]
        LOGGER.info(
            "Retrieved %d chunks in %.3fs from sources=%s",
            len(retrieved_chunks),
            elapsed,
            sources,
        )

        context_parts: list[str] = []
        for chunk in retrieved_chunks:
            context_parts.append(
                "\n".join(
                    [
                        f"[source={chunk.metadata.source}]",
                        f"[filename={chunk.metadata.filename}]",
                        f"[page={chunk.metadata.page}]",
                        f"[chunk_id={chunk.metadata.chunk_id}]",
                        chunk.text,
                    ]
                )
            )
        return "\n\n---\n\n".join(context_parts)

    def _build_user_prompt(self, topic: str, context: str) -> str:
        if not context:
            return f"Topic: {topic}"

        return (
            f"Topic: {topic}\n\n"
            "Knowledge Context (highest relevance first):\n"
            f"{context}\n\n"
            "Use the context when helpful. If context is insufficient, continue with general knowledge."
        )

    def generate(self, topic: str, director_plan: Dict[str, Any] | None = None) -> Dict[str, Any]:
        system_prompt = self._prompt_path.read_text(encoding="utf-8")
        context = self._build_context(topic)
        user_prompt = self._build_user_prompt(topic, context)
        if director_plan is not None and (research_focus := director_plan.get("research_focus")):
            user_prompt = f"{user_prompt}\nResearch focus: {research_focus}"
        return self.provider.generate_structured_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "audience": {"type": "string"},
                    "summary": {"type": "string"},
                    "insights": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["topic", "audience", "summary", "insights"],
            },
        )
