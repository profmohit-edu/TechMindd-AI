"""Text chunking utilities for RAG ingestion."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    """A single chunk of text with position metadata."""

    text: str
    chunk_id: int
    start_char: int
    end_char: int


class TextChunker:
    """Chunk long text into overlapping windows suitable for embedding."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def chunk(self, text: str) -> list[Chunk]:
        """Split text into deterministic overlapping chunks."""
        normalized = text.strip()
        if not normalized:
            return []

        chunks: list[Chunk] = []
        start = 0
        chunk_id = 0
        step = self._chunk_size - self._chunk_overlap

        while start < len(normalized):
            end = min(start + self._chunk_size, len(normalized))
            segment = normalized[start:end].strip()
            if segment:
                chunks.append(
                    Chunk(
                        text=segment,
                        chunk_id=chunk_id,
                        start_char=start,
                        end_char=end,
                    )
                )
                chunk_id += 1

            if end >= len(normalized):
                break
            start += step

        return chunks
