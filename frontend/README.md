# EuroPilot dashboard

This is the read-only React/Vite dashboard for the synthetic investigation API.

From `frontend/`, run `npm install`, then `npm run dev`. In local development, browser `/api` requests remain same-origin and Vite proxies them to `http://127.0.0.1:8000` by default. Set `VITE_API_BASE_URL=http://127.0.0.1:8001` (or `VITE_API_PROXY_TARGET`) to proxy to another local backend; this avoids browser CORS. The backend reports `sqlite_synthetic`; the dashboard uses local SQLite-backed synthetic records and does not represent them as production-ready persistence.
