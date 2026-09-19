# SIH 26184 - Investigator Frontend

Next.js (App Router) frontend for the Predictive Cybercrime Intelligence Platform.
Serves the demo journey: login → dashboard → alerts → case workspace → transactions →
network → prediction run → evidence → GIS risk map → investigator actions → audit log → logout.

## Setup

```bash
npm install
```

Environment (read at server start; secrets and cookie behaviour are managed server-side):

| Variable | Default | Purpose |
|----------|---------|---------|
| `BACKEND_URL` | `http://localhost:8000` | FastAPI backend. All `/api/*` data calls are proxied to it via `next.config.ts` rewrites using the same session cookie. |
| `SESSION_COOKIE_NAME` | `sih_access_token` | Name of the httpOnly session cookie; must match the backend's `SESSION_COOKIE_NAME`. |
| `ACCESS_TOKEN_TTL_HOURS` | `12` | Session lifetime (mirrors backend TTL). |

## Run

```bash
npm run dev            # http://localhost:3000
```

Start the backend first (see `backend/README.md`, incl. `DEMO_PASSWORD` + seed). Log in with one of
the seeded accounts (investigator `a.patil@cic.gov.in`, analyst, or admin — all share the seeded
`DEMO_PASSWORD`). The data plane (dashboard, cases, alerts, GIS, transactions, predictions) and the
audit log (admin-only) are served from the backend through `/api/*` rewrites; the session cookie set
by the login proxy is forwarded, so the browser never needs a raw token.

Pages that have no backend API yet (Predictions overview, Reports, Users) show clearly labelled
offline sample data.

## Checks

```bash
npm run lint
npm run build
```