"""Shared path and discovery helpers for RAG assets."""

from __future__ import annotations

import os
from pathlib import Path


SUPPORTED_DOCUMENT_SUFFIXES = {".pdf", ".docx", ".txt", ".md", ".markdown"}
_KNOWLEDGE_DIR_ENV = "TECHMINDD_KNOWLEDGE_DIR"


def resolve_documents_dir(documents_dir: Path | str | None = None) -> Path:
    """Resolve the knowledge documents directory to an absolute path."""
    raw_path = documents_dir or os.getenv(_KNOWLEDGE_DIR_ENV) or "knowledge/documents"
    return Path(raw_path).expanduser().resolve()


def resolve_embeddings_dir(documents_dir: Path | str | None = None) -> Path:
    """Resolve the embeddings directory adjacent to the knowledge documents directory."""
    return resolve_documents_dir(documents_dir).parent / "embeddings"


def set_active_documents_dir(documents_dir: Path | str) -> Path:
    """Persist the active knowledge documents directory for the current process."""
    resolved = resolve_documents_dir(documents_dir)
    os.environ[_KNOWLEDGE_DIR_ENV] = str(resolved)
    return resolved


def discover_documents(documents_dir: Path | str | None = None) -> list[Path]:
    """Recursively discover supported knowledge documents."""
    root = resolve_documents_dir(documents_dir)
    if not root.exists():
        return []

    return [
        path
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.suffix.lower() in SUPPORTED_DOCUMENT_SUFFIXES
    ]
