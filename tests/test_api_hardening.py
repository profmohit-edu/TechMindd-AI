from fastapi.responses import JSONResponse
from prometheus_client import generate_latest

from api.middleware import ProductionMiddleware
from api.routes import health


def test_health_has_observability_and_security_headers():
    payload = health()
    response = ProductionMiddleware._finalize(
        JSONResponse(payload.model_dump()), "test-request", "test-correlation"
    )

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "test-request"
    assert response.headers["x-correlation-id"] == "test-correlation"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_metrics_endpoint_exposes_service_health():
    assert b"techmindd_health" in generate_latest()


def test_topic_sanitization():
    from api.schemas import GenerateRequest

    request = GenerateRequest(topic="  Artificial\n Intelligence  ")
    assert request.topic == "Artificial Intelligence"
