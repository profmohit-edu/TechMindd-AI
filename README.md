# TechMindd-AI

TechMindd-AI is a production-oriented, workflow-driven content generation platform. A Director plans each run; dynamically discovered plugins generate, validate, score, and reflect on artifacts; the packaging layer emits Markdown, reports, metadata, a manifest, and a ZIP archive. It is available through a CLI, FastAPI service, and React dashboard.

## Capabilities

- YAML workflows and automatic plugin discovery
- OpenAI/Gemini provider failover with retry, timeout, token, and cost budgets
- RAG-assisted research over PDF, DOCX, text, and Markdown sources
- Validation, quality scoring, and reflection before atomic packaging
- Background REST jobs and a responsive React dashboard
- JSON logs, request/correlation IDs, Prometheus metrics, API keys, rate limits, CORS, and secure headers
- Non-root multi-stage containers and automated release gates

## Quick start

Requirements: Python 3.12+, Node.js 22+ for the dashboard, and at least one provider API key.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python factory.py --workflow youtube_package --topic "Artificial Intelligence"
```

Start the API and dashboard:

```bash
uvicorn api.app:app --reload
cd frontend
npm ci
npm run dev
```

Swagger is available at `http://localhost:8000/docs`; the dashboard defaults to `http://localhost:5173`.

## Containers

```bash
docker compose --profile production up --build
```

The API is exposed on port 8000 and the production dashboard on port 8080. For hot-reloading frontend development use `docker compose --profile development up --build`.

## Configuration

Copy `.env.example` and configure:

- `TECHMINDD_API_KEYS`: comma-separated API keys. Authentication is disabled only when empty, which is suitable for local development.
- `OPENAI_API_KEY`, `GEMINI_API_KEY`: provider credentials.
- `CORS_ORIGINS`: exact comma-separated browser origins.
- `RATE_LIMIT_PER_MINUTE`: per-client, per-process request limit.
- `LOG_LEVEL`, `LOG_FILE`: JSON logging configuration.
- Provider retry, timeout, token, and cost budgets are also available through CLI/configuration.

Clients authenticate with `X-API-Key`. Every response returns `X-Request-ID` and `X-Correlation-ID`; callers may supply either header to propagate distributed tracing context.
The dashboard stores its TechMindd API key only for the current browser session; provider credentials remain server-side.

## Operations

- Health: `GET /health`
- Metrics: `GET /metrics`
- OpenAPI: `GET /docs`
- Logs: JSON lines on stdout and rotating files under `logs/`
- Version: `VERSION`; image builds expose `BUILD_SHA` and `BUILD_DATE` in package metadata

Prometheus metrics cover HTTP traffic, health, active and completed generations, duration, provider calls, latency, tokens, and cost. Protect metrics using private networking or an authenticated monitoring proxy in public deployments.

## Documentation

- [Architecture](docs/architecture.md)
- [Deployment guide](docs/deployment.md)
- [API guide](docs/api.md)
- [Plugin developer guide](docs/plugin-development.md)
- [Security policy](SECURITY.md)
- [Changelog](CHANGELOG.md)

## Development and release gates

```bash
ruff check .
pytest -q
cd frontend && npm run build
docker build --target api-runtime -t techmindd-ai:1.0.1 .
```

GitHub Actions repeats lint, unit and integration tests, frontend compilation, dependency/static security scans, and the production image build. Releases follow Semantic Versioning; update `VERSION` and `CHANGELOG.md` together.

## License and contributions

Contributions should include tests and documentation for changed public behavior. Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md). Review the repository license before redistribution.
