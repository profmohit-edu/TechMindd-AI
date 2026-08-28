"""Grounded technical learning assistance built on TechMindd's RAG and providers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from pydantic import ValidationError

from api.schemas import LearningAssistantRequest, LearningAssistantResponse, LearningSource
from providers.provider_factory import ProviderFactory
from rag.embedder import SentenceTransformerEmbedder
from rag.ingestion import IngestionPipeline
from rag.paths import resolve_documents_dir, resolve_embeddings_dir
from rag.retriever import Retriever
from rag.vector_store import ChromaVectorStore

_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "explanation": {"type": "string"},
        "concepts": {"type": "array", "items": {"type": "string"}},
        "steps": {"type": "array", "items": {"type": "string"}},
        "example": {"type": "string"},
        "misconceptions": {"type": "array", "items": {"type": "string"}},
        "practice": {"type": "array", "items": {"type": "string"}},
        "next_learning": {"type": "array", "items": {"type": "string"}},
        "evidence_used": {"type": "array", "items": {"type": "integer"}},
    },
    "required": ["explanation", "concepts", "steps", "example", "misconceptions", "practice", "next_learning", "evidence_used"],
}


class LearningAssistant:
    """Retrieve trusted context and ask the configured provider for grounded tutoring."""

    def __init__(self, *, documents_dir: Path | None = None, provider_factory: Callable[[], Any] | None = None, top_k: int = 4) -> None:
        self.documents_dir = resolve_documents_dir(documents_dir or Path("knowledge/documents"))
        self.embeddings_dir = resolve_embeddings_dir(self.documents_dir)
        self.provider_factory = provider_factory or ProviderFactory().managed_provider
        self.top_k = top_k

    def answer(self, request: LearningAssistantRequest) -> LearningAssistantResponse:
        embedder = SentenceTransformerEmbedder()
        store = ChromaVectorStore(persist_directory=self.embeddings_dir)
        if store.count() == 0:
            IngestionPipeline(documents_dir=self.documents_dir, embeddings_dir=self.embeddings_dir, embedder=embedder, vector_store=store).ingest()

        retrieved = Retriever(vector_store=store, embedder=embedder).retrieve(
            f"{request.domain} {request.objective} {request.question}", top_k=self.top_k
        )
        usable = [item for item in retrieved if item.text.strip()]
        if not usable:
            raise ValueError("No knowledge context is available for this question")
        sources = [LearningSource(id=index, filename=item.metadata.filename, page=item.metadata.page, chunk_id=item.metadata.chunk_id, relevance=round(max(0.0, min(1.0, item.score)), 4), excerpt=item.text.strip()[:900]) for index, item in enumerate(usable, start=1)]
        context = "\n\n".join(f"[SOURCE {source.id}: {source.filename}, page {source.page}]\n{source.excerpt}" for source in sources)
        system_prompt = (
            "You are TechMindd's technical learning assistant. Use only supplied retrieved evidence for factual claims. "
            "Never invent a source. Explain at the learner's requested level. Return the required JSON structure. "
            "evidence_used must contain only SOURCE numbers directly supporting the explanation. State when evidence is insufficient."
        )
        user_prompt = f"Domain: {request.domain}\nLevel: {request.level}\nLearning objective: {request.objective}\nQuestion: {request.question}\n\nRETRIEVED EVIDENCE\n{context}"
        provider = self.provider_factory()
        generated = provider.generate_structured_json(system_prompt=system_prompt, user_prompt=user_prompt, response_schema=_RESPONSE_SCHEMA, temperature=0.1, max_output_tokens=1400)
        allowed_ids = {source.id for source in sources}
        try:
            response = LearningAssistantResponse(**generated, domain=request.domain, level=request.level, objective=request.objective, question=request.question, sources=sources, provider=str(getattr(provider, "model", "configured provider")))
        except ValidationError as exc:
            raise ValueError("The model returned an invalid learning response") from exc
        if not response.evidence_used or not set(response.evidence_used).issubset(allowed_ids):
            raise ValueError("The model response was not grounded in retrieved evidence")
        return response
