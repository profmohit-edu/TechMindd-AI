from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

from rag.embedder import SentenceTransformerEmbedder
from rag.ingestion import IngestionPipeline
from rag.paths import discover_documents
from rag.retriever import Retriever
from rag.vector_store import ChromaVectorStore


def _create_minimal_docx(path: Path, text: str) -> None:
    namespace = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{namespace}"><w:body>'
        f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>"
        "</w:body></w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>'
    )

    with ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("word/document.xml", document_xml)


def test_discover_documents_recurses_and_filters_supported_types(tmp_path: Path) -> None:
    docs_dir = tmp_path / "knowledge" / "documents"
    nested_dir = docs_dir / "nested"
    nested_dir.mkdir(parents=True)

    (docs_dir / "guide.md").write_text("AI guide", encoding="utf-8")
    (docs_dir / "notes.txt").write_text("AI notes", encoding="utf-8")
    (nested_dir / "paper.pdf").write_bytes(b"%PDF-1.4\n")
    _create_minimal_docx(nested_dir / "report.docx", "AI report")
    (nested_dir / "ignore.png").write_bytes(b"png")

    discovered = discover_documents(docs_dir)

    assert sorted(path.name for path in discovered) == ["guide.md", "notes.txt", "paper.pdf", "report.docx"]


def test_docx_ingestion_indexes_chunks_and_incremental_runs_skip_unchanged_files(tmp_path: Path) -> None:
    docs_dir = tmp_path / "knowledge" / "documents"
    docs_dir.mkdir(parents=True)
    _create_minimal_docx(docs_dir / "ai.docx", "Artificial intelligence improves automation.")

    pipeline = IngestionPipeline(
        documents_dir=docs_dir,
        embeddings_dir=tmp_path / "knowledge" / "embeddings",
        embedder=SentenceTransformerEmbedder(model_name="BAAI/bge-small-en-v1.5", force_offline_fallback=True),
    )

    first_report = pipeline.ingest()
    second_report = pipeline.ingest()

    assert first_report.detected_documents == 1
    assert first_report.ingested_files == 1
    assert first_report.indexed_chunks > 0
    assert second_report.detected_documents == 1
    assert second_report.ingested_files == 0
    assert second_report.indexed_chunks == 0


def test_retrieval_returns_relevant_chunks(tmp_path: Path) -> None:
    docs_dir = tmp_path / "knowledge" / "documents"
    docs_dir.mkdir(parents=True)
    (docs_dir / "ai.md").write_text(
        "Artificial intelligence uses machine learning, neural networks, and data-driven reasoning.",
        encoding="utf-8",
    )
    (docs_dir / "gardening.txt").write_text(
        "Gardening relies on soil, compost, watering, and seasonal planting.",
        encoding="utf-8",
    )

    embeddings_dir = tmp_path / "knowledge" / "embeddings"
    embedder = SentenceTransformerEmbedder(model_name="BAAI/bge-small-en-v1.5", force_offline_fallback=True)
    pipeline = IngestionPipeline(
        documents_dir=docs_dir,
        embeddings_dir=embeddings_dir,
        embedder=embedder,
    )
    report = pipeline.ingest()

    store = ChromaVectorStore(persist_directory=embeddings_dir)
    retriever = Retriever(vector_store=store, embedder=embedder)
    results = retriever.retrieve("Artificial Intelligence", top_k=2)

    assert report.indexed_chunks >= 2
    assert len(results) == 2
    assert results[0].metadata.filename == "ai.md"
