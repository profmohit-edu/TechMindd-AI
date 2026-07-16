"""No-op Chroma telemetry client to suppress noisy telemetry failures."""

from __future__ import annotations

from chromadb.telemetry.product import ProductTelemetryClient, ProductTelemetryEvent
from overrides import override

TELEMETRY_IMPL = "rag.chroma_telemetry.NoOpProductTelemetry"


class NoOpProductTelemetry(ProductTelemetryClient):
    """Disable Chroma telemetry cleanly."""

    @override
    def capture(self, event: ProductTelemetryEvent) -> None:
        pass
