"""Embedding backend for RAG using sentence-transformers."""

from __future__ import annotations

import hashlib
import logging
import math
import re
from typing import Sequence

from sentence_transformers import SentenceTransformer

LOGGER = logging.getLogger("techmindd.rag.embedder")
# Sample three 4-byte slices from the SHA-256 digest to spread each token across
# multiple dimensions while keeping the fallback embedder fast and deterministic.
_HASH_SAMPLE_BYTES = 12
_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


class SentenceTransformerEmbedder:
    """Encode text into dense vectors via sentence-transformers."""

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
        fallback_dimensions: int = 384,
        force_offline_fallback: bool = False,
    ) -> None:
        self._model_name = model_name
        self._fallback_dimensions = fallback_dimensions
        self._model: SentenceTransformer | None = None
        if force_offline_fallback:
            LOGGER.info(
                "Using local hashing embedder in forced offline mode for model: %s", model_name
            )
            return
        try:
            self._model = SentenceTransformer(model_name, local_files_only=True)
            LOGGER.info("Loaded sentence-transformers model: %s", model_name)
        except (OSError, RuntimeError, ValueError) as exc:
            LOGGER.warning(
                "Falling back to local hashing embedder because sentence-transformers model '%s' was unavailable: %s",
                model_name,
                exc,
            )

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed multiple documents."""
        if not texts:
            return []
        if self._model is not None:
            vectors = self._model.encode(list(texts), normalize_embeddings=True)
            return [vector.tolist() for vector in vectors]
        return [self._fallback_embed(text) for text in texts]

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query string."""
        if self._model is not None:
            vector = self._model.encode(query, normalize_embeddings=True)
            return vector.tolist()
        return self._fallback_embed(query)

    def _fallback_embed(self, text: str) -> list[float]:
        vector = [0.0] * self._fallback_dimensions
        tokens = _TOKEN_PATTERN.findall(text.lower())

        if not tokens:
            vector[0] = 1.0
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            for offset in range(0, _HASH_SAMPLE_BYTES, 4):
                index = (
                    int.from_bytes(digest[offset : offset + 4], "big") % self._fallback_dimensions
                )
                # Flip the sign based on the sampled byte so hashed terms distribute
                # across the vector space instead of only accumulating positive counts.
                sign = 1.0 if digest[offset + 3] % 2 == 0 else -1.0
                vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            vector[0] = 1.0
            return vector
        return [value / norm for value in vector]
