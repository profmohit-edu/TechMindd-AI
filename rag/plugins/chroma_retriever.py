"""Chroma-based retriever plugin."""

from __future__ import annotations

import logging
from pathlib import Path

import config
from rag.plugins.base import BaseRetrieverPlugin
from rag.retriever import Retriever
from rag.vector_store import ChromaVectorStore


LOGGER = logging.getLogger("techmindd.retrievers.chroma")


class ChromaRetrieverPlugin(BaseRetrieverPlugin):
    """Instantiate retriever backed by ChromaVectorStore."""

    retriever_name = "chroma"

    def build(self) -> Retriever | None:
        if not config.settings.rag_enabled:
            LOGGER.info("RAG disabled by configuration")
            return None

        store_dir = Path("knowledge/embeddings")
        if not store_dir.exists():
            LOGGER.info("Knowledge embeddings directory not found; RAG disabled for this run")
            return None

        try:
            store = ChromaVectorStore(persist_directory=store_dir)
            return Retriever(vector_store=store)
        except Exception:
            LOGGER.exception("Failed to initialize retriever; continuing without RAG")
            return None

