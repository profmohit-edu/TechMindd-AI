"""Embedding backend for RAG using sentence-transformers."""

from __future__ import annotations

from typing import Sequence

from sentence_transformers import SentenceTransformer


class SentenceTransformerEmbedder:
    """Encode text into dense vectors via sentence-transformers."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5") -> None:
        self._model = SentenceTransformer(model_name)

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed multiple documents."""
        if not texts:
            return []
        vectors = self._model.encode(list(texts), normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query string."""
        vector = self._model.encode(query, normalize_embeddings=True)
        return vector.tolist()
