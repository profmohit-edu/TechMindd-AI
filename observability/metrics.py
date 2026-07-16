"""Prometheus metrics for API and generation operations."""

from prometheus_client import Counter, Gauge, Histogram


HTTP_REQUESTS = Counter(
    "techmindd_http_requests_total",
    "HTTP requests",
    ("method", "path", "status"),
)
HTTP_LATENCY = Histogram(
    "techmindd_http_request_duration_seconds",
    "HTTP request latency",
    ("method", "path"),
)
HEALTH = Gauge("techmindd_health", "Service health (1=healthy)")
ACTIVE_JOBS = Gauge("techmindd_active_jobs", "Queued and running generation jobs")
GENERATION_JOBS = Counter(
    "techmindd_generation_jobs_total",
    "Generation jobs by terminal status",
    ("status", "workflow"),
)
GENERATION_DURATION = Histogram(
    "techmindd_generation_duration_seconds",
    "Generation job duration",
    ("workflow",),
)
PROVIDER_REQUESTS = Counter(
    "techmindd_provider_requests_total",
    "Provider attempts",
    ("provider", "status"),
)
PROVIDER_LATENCY = Histogram(
    "techmindd_provider_latency_seconds",
    "Provider generation latency",
    ("provider",),
)
PROVIDER_TOKENS = Counter(
    "techmindd_provider_tokens_total",
    "Provider tokens consumed",
    ("provider", "direction"),
)
PROVIDER_COST = Counter(
    "techmindd_provider_estimated_cost_usd_total",
    "Estimated provider cost in USD",
    ("provider",),
)
