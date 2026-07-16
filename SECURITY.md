# Security Policy

## Supported versions

Security fixes are provided for the latest `1.x` release.

## Reporting a vulnerability

Do not open a public issue. Use GitHub's private vulnerability reporting for this repository and include reproduction steps, affected versions, and impact. Maintainers will acknowledge reports within three business days and coordinate disclosure after a fix is available.

## Deployment baseline

- Configure one or more high-entropy values in `TECHMINDD_API_KEYS`.
- Store provider keys in a secret manager, never in source control or images.
- Terminate TLS at a trusted reverse proxy and restrict `/metrics` at the network layer.
- Set explicit `CORS_ORIGINS`, token/cost budgets, and rate limits.
- Keep the container non-root and mount runtime data on dedicated volumes.
