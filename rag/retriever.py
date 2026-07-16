"""Retriever API for RAG queries."""

from __future__ import annotations

from dataclasses import dataclass

from rag.embedder import SentenceTransformerEmbedder
from rag.vector_store import ChunkMetadata, ChromaVectorStore


@dataclass(frozen=True)
class RetrievedChunk:
    """Retrieved chunk payload returned by retriever."""

    text: str
    metadata: ChunkMetadata
    score: float


class Retriever:
    """Top-k retriever over the vector store."""

    def __init__(
        self,
        vector_store: ChromaVectorStore,
        embedder: SentenceTransformerEmbedder | None = None,
    ) -> None:
        self._vector_store = vector_store
        self._embedder = embedder or SentenceTransformerEmbedder()

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        """Retrieve relevant chunks for a query."""
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")

        embedding = self._embedder.embed_query(query)
        rows = self._vector_store.query(query_embedding=embedding, top_k=top_k)

        results: list[RetrievedChunk] = []
        for row in rows:
            raw_meta = row["metadata"]
            metadata = ChunkMetadata(
                filename=str(raw_meta.get("filename", "")),
                page=int(raw_meta.get("page", 0)),
                chunk_id=int(raw_meta.get("chunk_id", 0)),
                source=str(raw_meta.get("source", "")),
            )
            distance = float(row.get("distance", 0.0))
            score = 1.0 - distance
            results.append(
                RetrievedChunk(
                    text=str(row.get("text", "")),
                    metadata=metadata,
                    score=score,
                )
            )
        return results
