"""Document ingestion pipeline for RAG knowledge base."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile

from defusedxml import ElementTree
from pypdf import PdfReader

from rag.chunker import TextChunker
from rag.embedder import SentenceTransformerEmbedder
from rag.paths import discover_documents, resolve_documents_dir, resolve_embeddings_dir
from rag.vector_store import ChromaVectorStore, ChunkMetadata

LOGGER = logging.getLogger("techmindd.rag.ingestion")
_MAX_DOCX_XML_SIZE_BYTES = 5_000_000


@dataclass(frozen=True)
class SourceDocument:
    """A parsed source document."""

    source: Path
    page: int
    text: str


@dataclass(frozen=True)
class IngestionReport:
    """Summary of a single ingestion run."""

    detected_documents: int
    ingested_files: int
    indexed_chunks: int
    removed_sources: int


class IngestionPipeline:
    """Ingest supported documents into Chroma vector store."""

    def __init__(
        self,
        documents_dir: Path = Path("knowledge/documents"),
        embeddings_dir: Path | None = None,
        chunker: TextChunker | None = None,
        embedder: SentenceTransformerEmbedder | None = None,
        vector_store: ChromaVectorStore | None = None,
    ) -> None:
        self._documents_dir = resolve_documents_dir(documents_dir)
        self._embeddings_dir = (
            resolve_embeddings_dir(self._documents_dir)
            if embeddings_dir is None
            else Path(embeddings_dir).expanduser().resolve()
        )
        self._chunker = chunker or TextChunker()
        self._embedder = embedder or SentenceTransformerEmbedder()
        self._vector_store = vector_store or ChromaVectorStore(
            persist_directory=self._embeddings_dir
        )
        self._state_path = self._embeddings_dir / "ingestion_state.json"

    def ingest(self, documents_path: Path | None = None) -> IngestionReport:
        """Ingest changed documents only."""
        target_dir = resolve_documents_dir(documents_path or self._documents_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        self._embeddings_dir.mkdir(parents=True, exist_ok=True)
        discovered_documents = discover_documents(target_dir)
        LOGGER.info("Detected %d documents in %s", len(discovered_documents), target_dir)

        previous_state = self._load_state()
        next_state: dict[str, str] = {}

        ingested_files = 0
        indexed_chunks = 0
        for file_path in discovered_documents:
            source = str(file_path.resolve())
            digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
            next_state[source] = digest

            if previous_state.get(source) == digest:
                continue

            self._vector_store.delete_by_source(source)
            chunk_count = self._ingest_single_file(file_path)
            ingested_files += 1
            indexed_chunks += chunk_count
            LOGGER.info("Ingested file: %s", file_path)

        removed_sources = set(previous_state).difference(next_state)
        for removed_source in removed_sources:
            self._vector_store.delete_by_source(removed_source)
            LOGGER.info("Removed stale source from index: %s", removed_source)

        self._save_state(next_state)
        LOGGER.info("Indexed %d chunks", indexed_chunks)
        return IngestionReport(
            detected_documents=len(discovered_documents),
            ingested_files=ingested_files,
            indexed_chunks=indexed_chunks,
            removed_sources=len(removed_sources),
        )

    def _ingest_single_file(self, path: Path) -> int:
        docs = self._parse_file(path)

        ids: list[str] = []
        texts: list[str] = []
        metadatas: list[ChunkMetadata] = []

        for doc in docs:
            chunks = self._chunker.chunk(doc.text)
            for chunk in chunks:
                ids.append(f"{doc.source.resolve()}::{doc.page}::{chunk.chunk_id}")
                texts.append(chunk.text)
                metadatas.append(
                    ChunkMetadata(
                        filename=doc.source.name,
                        page=doc.page,
                        chunk_id=chunk.chunk_id,
                        source=str(doc.source.resolve()),
                    )
                )

        if not texts:
            return 0

        embeddings = self._embedder.embed_documents(texts)
        self._vector_store.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        LOGGER.info("Chunks created for %s: %d", path.name, len(texts))
        return len(texts)

    def _parse_file(self, path: Path) -> list[SourceDocument]:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return self._parse_pdf(path)
        if suffix == ".docx":
            return self._parse_docx(path)
        return [
            SourceDocument(
                source=path,
                page=1,
                text=path.read_text(encoding="utf-8", errors="ignore"),
            )
        ]

    def _parse_pdf(self, path: Path) -> list[SourceDocument]:
        reader = PdfReader(str(path))
        docs: list[SourceDocument] = []
        for idx, page in enumerate(reader.pages, start=1):
            docs.append(
                SourceDocument(
                    source=path,
                    page=idx,
                    text=page.extract_text() or "",
                )
            )
        return docs

    def _parse_docx(self, path: Path) -> list[SourceDocument]:
        namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        with ZipFile(path) as archive:
            info = archive.getinfo("word/document.xml")
            if info.file_size > _MAX_DOCX_XML_SIZE_BYTES:
                raise ValueError(
                    f"DOCX document.xml exceeds limit: {info.file_size} bytes > "
                    f"{_MAX_DOCX_XML_SIZE_BYTES} bytes: {path}"
                )
            document_xml = archive.read("word/document.xml")

        root = ElementTree.fromstring(document_xml)
        paragraphs: list[str] = []
        for paragraph in root.findall(".//w:p", namespace):
            text_parts = [node.text or "" for node in paragraph.findall(".//w:t", namespace)]
            text = "".join(text_parts).strip()
            if text:
                paragraphs.append(text)

        return [
            SourceDocument(
                source=path,
                page=0,
                text="\n\n".join(paragraphs),
            )
        ]

    def _load_state(self) -> dict[str, str]:
        if not self._state_path.exists():
            return {}
        try:
            raw = json.loads(self._state_path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                return {}
            return {str(k): str(v) for k, v in raw.items()}
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_state(self, state: dict[str, str]) -> None:
        self._state_path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
