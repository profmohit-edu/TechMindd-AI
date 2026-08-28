from __future__ import annotations

from pathlib import Path

import pytest

from api.schemas import LearningAssistantRequest
from learning.service import LearningAssistant


class FakeProvider:
    model = "test-grounded-model"

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.prompts: list[str] = []

    def generate_structured_json(self, **request):
        if self.fail:
            raise TimeoutError("provider unavailable")
        self.prompts.append(request["user_prompt"])
        topic = "backpropagation" if "backpropagation" in request["user_prompt"].lower() else "predictive maintenance"
        return {
            "explanation": f"A grounded explanation of {topic} using the retrieved engineering evidence.",
            "concepts": [topic, "evidence grounding"],
            "steps": ["Inspect the retrieved context", "Apply the concept"],
            "example": f"A worked {topic} example based on source 1.",
            "misconceptions": ["Generated prose is not itself source evidence."],
            "practice": [f"Explain one consequence of {topic}."],
            "next_learning": ["Compare the result with another technical case."],
            "evidence_used": [1],
        }


def _documents(tmp_path: Path) -> Path:
    documents = tmp_path / "knowledge" / "documents"
    documents.mkdir(parents=True)
    (documents / "ai.md").write_text(
        "Backpropagation computes gradients through a neural network. Gradient descent updates weights to reduce a loss function.",
        encoding="utf-8",
    )
    (documents / "engineering.txt").write_text(
        "Predictive maintenance uses equipment sensor signals and anomaly detection to identify developing faults before failure.",
        encoding="utf-8",
    )
    return documents


def test_learning_query_retrieves_context_and_returns_structured_grounding(tmp_path: Path) -> None:
    provider = FakeProvider()
    assistant = LearningAssistant(documents_dir=_documents(tmp_path), provider_factory=lambda: provider, top_k=2)
    response = assistant.answer(LearningAssistantRequest(question="How do gradient descent and backpropagation work together?", objective="Understand neural network learning", domain="Artificial Intelligence", level="beginner"))

    assert response.provider == "test-grounded-model"
    assert response.sources
    assert response.evidence_used == [1]
    assert "SOURCE 1" in provider.prompts[0]
    assert response.practice and response.next_learning


def test_different_queries_produce_different_assistance(tmp_path: Path) -> None:
    provider = FakeProvider()
    assistant = LearningAssistant(documents_dir=_documents(tmp_path), provider_factory=lambda: provider, top_k=2)
    ai = assistant.answer(LearningAssistantRequest(question="Explain backpropagation with gradient descent.", objective="Learn network training", domain="Artificial Intelligence", level="beginner"))
    maintenance = assistant.answer(LearningAssistantRequest(question="How does anomaly detection support equipment maintenance?", objective="Plan predictive maintenance", domain="Engineering Applications", level="intermediate"))

    assert ai.explanation != maintenance.explanation
    assert ai.question != maintenance.question


def test_invalid_input_is_rejected() -> None:
    with pytest.raises(ValueError):
        LearningAssistantRequest(question="short", objective="AI", domain="AI")


def test_provider_failure_is_not_replaced_with_fixed_demo_output(tmp_path: Path) -> None:
    assistant = LearningAssistant(documents_dir=_documents(tmp_path), provider_factory=lambda: FakeProvider(fail=True))
    with pytest.raises(TimeoutError, match="provider unavailable"):
        assistant.answer(LearningAssistantRequest(question="Explain backpropagation and gradient descent.", objective="Understand training", domain="Artificial Intelligence"))


def test_ungrounded_model_response_is_rejected(tmp_path: Path) -> None:
    class UngroundedProvider(FakeProvider):
        def generate_structured_json(self, **request):
            response = super().generate_structured_json(**request)
            response["evidence_used"] = [99]
            return response

    assistant = LearningAssistant(documents_dir=_documents(tmp_path), provider_factory=UngroundedProvider)
    with pytest.raises(ValueError, match="not grounded"):
        assistant.answer(LearningAssistantRequest(question="Explain backpropagation and gradient descent.", objective="Understand training", domain="Artificial Intelligence"))
