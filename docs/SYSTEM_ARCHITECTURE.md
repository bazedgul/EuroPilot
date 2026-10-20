# System Architecture

Status: Proposed; owner approval required.

## Proposed shape

Use a modular monolith: React/TypeScript/Vite/Tailwind frontend; Python/Django/DRF backend; PostgreSQL persistence; an adapter boundary for AI with local Ollama preferred for development; pytest, frontend tests, API tests, selected Playwright tests, and GitHub Actions subject to repository limits.

The backend should separate API validation/orchestration, domain rules, persistence, provider-event adapters, and AI explanation adapters. Core investigation must function without AI.

## Trade-offs

This keeps deployment and consistency simpler than microservices while leaving boundaries for later extraction. PostgreSQL supports constraints and transactional correlation. Ollama reduces mandatory external-data transfer and per-request cost, but model availability and quality vary. React/Vite offers a common browser workflow but requires explicit accessibility and state handling.

No package installation, service, broker, Celery, Redis, external AI API, or real provider integration is approved by this document.

## Approval questions

Confirm versions, tenancy model, deployment target, API style/versioning, and whether local development requires Docker Compose. These affect setup and operational constraints.
