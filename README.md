# EuroPilot

EuroPilot is an early-stage concept for an AI-assisted payment incident investigation and reconciliation platform. The current local MVP is a synthetic-data, deterministic, read-only investigation workflow; it does not execute payments or move money.

The repository contains the Phase 0 documentation foundation and a local Django/SQLite backend with a React/Vite investigation dashboard. These are demo-scope implementations, not production readiness claims.

Start with:

- [Project source of truth](docs/PROJECT_SOURCE_OF_TRUTH.md)
- [Product brief](docs/PRODUCT_BRIEF.md)
- [Requirements](docs/REQUIREMENTS.md)
- [Phase 0 plan](docs/phases/PHASE_00_FOUNDATION.md)
- [Feature registry](docs/features/FEATURE_REGISTRY.md)

## Local demo setup

From the repository root, prepare the SQLite database and synthetic records:

```powershell
$env:PYTHONPATH="backend"
$env:DJANGO_SETTINGS_MODULE="europilot.settings"
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 127.0.0.1:8000
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1
```

The Vite development proxy sends `/api` requests to `http://127.0.0.1:8000`. Set `VITE_API_BASE_URL` when using another backend URL. The seed command is idempotent and does not replace existing records. SQLite data is local synthetic demo data only.

## Read-only API

- `GET /api/health/` — service status and `sqlite_synthetic` data mode.
- `GET /api/v1/investigations/` — bounded list response with `page`, `page_size`, `count`, and `results`.
- `GET /api/v1/investigations/<id>/` — one investigation with outcome, attempts, deliveries, evidence, provenance, and missing-evidence reasons.

The API has no payment execution, money movement, refund, reversal, cancellation, approval, live-provider, or AI-authoritative endpoints.

## Verification

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --check
python -m pytest -q
python -m compileall -q backend tests
cd frontend
npm test
npm run build
```

Automated checks cover the deterministic domain, persisted constraints, seed idempotency, API behavior, and frontend rendering. Visual browser verification remains a manual follow-up when a browser automation tool is available; it has not been claimed as completed.

## Current limitations

The demo uses synthetic data, local SQLite persistence, and local/demo access assumptions. It has no live payment providers, real money movement, production authentication or tenancy, compliance certification, or production-grade operational guarantees. AI is not used for authoritative decisions.
