# Deployment guide

## Production prerequisites

Use Docker 24+ with Compose v2, persistent storage, TLS termination, a secret manager, and outbound access to configured providers. Copy `.env.example` to a deployment-specific secret source; never bake `.env` into an image.

## Docker Compose

```bash
export TECHMINDD_API_KEYS="$(openssl rand -hex 32)"
export OPENAI_API_KEY="..."
export CORS_ORIGINS="https://ai.example.com"
docker compose --profile production up --build -d
docker compose ps
curl http://localhost:8000/health
```

The API container runs as an unprivileged user. Compose persists `knowledge/`, `output/`, and `logs/`. Back up these paths according to retention requirements. The frontend reverse-proxies `/api` to the API service.

## Development profile

```bash
docker compose --profile development up --build
```

This starts Vite with source mounts while retaining the same containerized API.

## Kubernetes or managed containers

Build the `api-runtime` target, inject secrets as environment variables, mount persistent volumes, and probe `/health`. Build `frontend-runtime` separately or publish `frontend/dist` through a CDN. Set `BUILD_SHA` and `BUILD_DATE` during the API image build. Run one API worker for v1.0 because background jobs are held in process memory.

## Monitoring and logging

Scrape `/metrics` every 15–30 seconds from a private network. Alert on an unhealthy gauge, elevated HTTP 5xx rate, generation failures, provider failures, latency, and budget exhaustion. Collect stdout JSON or `logs/techmindd.jsonl`; rotation defaults are configurable with `LOG_MAX_BYTES` and `LOG_BACKUP_COUNT`.

## Security checklist

1. Terminate HTTPS and redirect HTTP.
2. Set high-entropy `TECHMINDD_API_KEYS` and exact `CORS_ORIGINS`.
3. Keep `/metrics` and provider credentials private.
4. Configure provider token and cost budgets.
5. Run automated image/dependency scanning and patch regularly.
6. Test restore procedures for knowledge and package volumes.

## Rollback

Deploy immutable semantic-version/image-SHA tags. To roll back, restore the previous image tag without replacing persistent volumes, confirm `/health`, run a canary generation, and inspect generation/provider metrics.
