"""Correlation, authentication, rate limiting, metrics, and headers."""

from __future__ import annotations

import logging
import os
import secrets
import threading
import time
from collections import defaultdict, deque
from re import compile
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from observability.context import correlation_id, request_id
from observability.metrics import HTTP_LATENCY, HTTP_REQUESTS

_PUBLIC_PATHS = {"/health", "/metrics", "/docs", "/openapi.json", "/redoc"}
_TRACE_ID_PATTERN = compile(r"^[A-Za-z0-9._:-]{1,128}$")
logger = logging.getLogger("techmindd.http")


class ProductionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._api_keys = {
            item.strip() for item in os.getenv("TECHMINDD_API_KEYS", "").split(",") if item.strip()
        }
        self._limit = max(1, int(os.getenv("RATE_LIMIT_PER_MINUTE", "120")))
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()
        self._last_cleanup = time.monotonic()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        req_id = self._trace_id(request.headers.get("X-Request-ID"))
        corr_id = self._trace_id(request.headers.get("X-Correlation-ID"), default=req_id)
        request_token = request_id.set(req_id)
        correlation_token = correlation_id.set(corr_id)
        started = time.monotonic()
        path = request.url.path
        status_code = 500
        try:
            if self._api_keys and path not in _PUBLIC_PATHS:
                supplied = request.headers.get("X-API-Key", "")
                if not any(secrets.compare_digest(supplied, key) for key in self._api_keys):
                    response = self._finalize(
                        JSONResponse({"detail": "Invalid API key"}, 401), req_id, corr_id
                    )
                    status_code = response.status_code
                    return response
            if path not in _PUBLIC_PATHS and not self._allow_request(
                request.client.host if request.client else "unknown"
            ):
                response = self._finalize(
                    JSONResponse({"detail": "Rate limit exceeded"}, 429), req_id, corr_id
                )
                status_code = response.status_code
                return response
            response = await call_next(request)
            status_code = response.status_code
            route = request.scope.get("route")
            path = str(getattr(route, "path", path))
            return self._finalize(response, req_id, corr_id)
        finally:
            elapsed = time.monotonic() - started
            metric_path = self._metric_path(path)
            HTTP_REQUESTS.labels(request.method, metric_path, str(status_code)).inc()
            HTTP_LATENCY.labels(request.method, metric_path).observe(elapsed)
            logger.info(
                "request_completed",
                extra={
                    "method": request.method,
                    "path": metric_path,
                    "status_code": status_code,
                    "latency_ms": round(elapsed * 1000, 2),
                    "client": request.client.host if request.client else "unknown",
                },
            )
            request_id.reset(request_token)
            correlation_id.reset(correlation_token)

    def _allow_request(self, client: str) -> bool:
        now = time.monotonic()
        with self._lock:
            if now - self._last_cleanup >= 60:
                stale_clients = [
                    key
                    for key, values in self._requests.items()
                    if not values or now - values[-1] >= 60
                ]
                for key in stale_clients:
                    del self._requests[key]
                self._last_cleanup = now
            entries = self._requests[client]
            while entries and now - entries[0] >= 60:
                entries.popleft()
            if len(entries) >= self._limit:
                return False
            entries.append(now)
            return True

    @staticmethod
    def _trace_id(value: str | None, default: str | None = None) -> str:
        if value and _TRACE_ID_PATTERN.fullmatch(value):
            return value
        return default or uuid4().hex

    @staticmethod
    def _metric_path(path: str) -> str:
        if path in _PUBLIC_PATHS or "{" in path:
            return path
        if path in {"/generate", "/jobs", "/workflows", "/plugins", "/providers"}:
            return path
        if path.startswith("/jobs/"):
            return "/jobs/{job_id}"
        if path.startswith("/knowledge/"):
            return "/knowledge/{operation}"
        return "/unmatched"

    @staticmethod
    def _finalize(response: Response, req_id: str, corr_id: str) -> Response:
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Correlation-ID"] = corr_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; frame-ancestors 'none'; object-src 'none'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://fastapi.tiangolo.com"
        )
        return response
