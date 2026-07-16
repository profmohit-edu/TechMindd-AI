"""Base retriever plugin abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod

from rag.retriever import Retriever


class BaseRetrieverPlugin(ABC):
    """Build retriever instances from plugin implementations."""

    retriever_name: str = ""

    @abstractmethod
    def build(self) -> Retriever | None:
        """Return a retriever instance or None when unavailable."""
        raise NotImplementedError

