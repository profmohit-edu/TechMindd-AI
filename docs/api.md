# API guide

The interactive OpenAPI specification is served at `/docs`. Unless no keys are configured for local development, send `X-API-Key` on protected routes. Send `X-Request-ID` and `X-Correlation-ID` to preserve tracing context; generated values are returned when omitted.

## Generate and poll

```bash
curl -X POST http://localhost:8000/generate \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-key' \
  -d '{"topic":"Artificial Intelligence","workflow":"youtube_package","provider":"auto"}'

curl -H 'X-API-Key: your-key' http://localhost:8000/jobs/JOB_ID
curl -H 'X-API-Key: your-key' http://localhost:8000/jobs/JOB_ID/result
```

`POST /generate` returns HTTP 202. Poll the job until `completed` or `failed`; the result endpoint returns HTTP 409 while incomplete. Download URLs point to individual immutable package files. `POST /jobs/{id}/retry` creates a new execution for a failed job.

## Discovery and operations

- `GET /workflows`: available YAML workflows.
- `GET /plugins`: discovered plugins.
- `GET /providers`: configured providers and health.
- `POST /knowledge/upload`: PDF, DOCX, TXT, Markdown; maximum 20 MB.
- `POST /knowledge/reindex`: rebuild the knowledge index.
- `GET /health`: unauthenticated liveness/readiness response.
- `GET /metrics`: Prometheus exposition format.

HTTP 401 indicates a missing/invalid key, 429 a rate-limit violation, 422 invalid input/configuration, and 409 a result requested before completion. Error bodies follow FastAPI's `{"detail": ...}` convention.
