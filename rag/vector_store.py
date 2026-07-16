"""ChromaDB vector store adapter for RAG."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings

from rag.chroma_telemetry import TELEMETRY_IMPL


@dataclass(frozen=True)
class ChunkMetadata:
    """Metadata attached to each embedded chunk."""

    filename: str
    page: int
    chunk_id: int
    source: str


class ChromaVectorStore:
    """Persistence and retrieval wrapper around ChromaDB."""

    def __init__(
        self,
        persist_directory: Path,
        collection_name: str = "techmindd_knowledge",
    ) -> None:
        self._persist_directory = persist_directory
        self._persist_directory.mkdir(parents=True, exist_ok=True)
        settings = Settings(
            anonymized_telemetry=False,
            is_persistent=True,
            persist_directory=str(self._persist_directory),
            chroma_product_telemetry_impl=TELEMETRY_IMPL,
            chroma_telemetry_impl=TELEMETRY_IMPL,
        )
        self._client = chromadb.PersistentClient(
            path=str(self._persist_directory), settings=settings
        )
        self._collection: Collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(
        self,
        ids: Sequence[str],
        documents: Sequence[str],
        embeddings: Sequence[Sequence[float]],
        metadatas: Sequence[ChunkMetadata],
    ) -> None:
        """Insert or update vectors and metadata."""
        self._collection.upsert(
            ids=list(ids),
            documents=list(documents),
            embeddings=[list(vector) for vector in embeddings],
            metadatas=[
                {
                    "filename": metadata.filename,
                    "page": metadata.page,
                    "chunk_id": metadata.chunk_id,
                    "source": metadata.source,
                }
                for metadata in metadatas
            ],
        )

    def delete_by_source(self, source: str) -> None:
        """Delete all chunks for a source file."""
        self._collection.delete(where={"source": source})

    def query(
        self,
        query_embedding: Sequence[float],
        top_k: int,
    ) -> list[dict[str, Any]]:
        """Query nearest neighbors by embedding."""
        response = self._collection.query(
            query_embeddings=[list(query_embedding)],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        documents = response.get("documents", [[]])[0]
        metadatas = response.get("metadatas", [[]])[0]
        distances = response.get("distances", [[]])[0]

        results: list[dict[str, Any]] = []
        for text, metadata, distance in zip(documents, metadatas, distances, strict=True):
            results.append(
                {
                    "text": text,
                    "metadata": metadata,
                    "distance": distance,
                }
            )
        return results

    def count(self) -> int:
        """Return the number of indexed chunks."""
        return int(self._collection.count())
