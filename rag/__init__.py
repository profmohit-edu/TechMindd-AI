"""Lazy RAG exports keep API health/startup independent of model loading."""

from __future__ import annotations

from importlib import import_module

_EXPORTS = {
    "Chunk": ("rag.chunker", "Chunk"),
    "TextChunker": ("rag.chunker", "TextChunker"),
    "SentenceTransformerEmbedder": ("rag.embedder", "SentenceTransformerEmbedder"),
    "IngestionPipeline": ("rag.ingestion", "IngestionPipeline"),
    "RetrievedChunk": ("rag.retriever", "RetrievedChunk"),
    "Retriever": ("rag.retriever", "Retriever"),
    "ChunkMetadata": ("rag.vector_store", "ChunkMetadata"),
    "ChromaVectorStore": ("rag.vector_store", "ChromaVectorStore"),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module_name, attribute = _EXPORTS[name]
    value = getattr(import_module(module_name), attribute)
    globals()[name] = value
    return value
