# SIH 26184 - Predictive Cybercrime Intelligence Platform (Prototype)

Full-stack prototype: `FastAPI + PostgreSQL/PostGIS` backend with an ML-backed ATM risk model, and a
`Next.js` investigator frontend. Authentication (opaque sessions + RBAC) and a full audit log are
enabled end to end.

## Layout

```text
backend/    FastAPI API, model service, migrations, seed, tests, smoke test
frontend/   Next.js investigator UI (App Router)
docs/       Blueprint + ML notes (training script is intentionally untracked)
```

## Prerequisites

- Docker (PostGIS) — `backend/docker-compose.yml`
- Python 3.11+, Node 20+
- Model artifact: copy `rf_baseline_model.joblib` into `backend/ml/` (gitignored; the API runs in
  degraded mode without it)

## Quick start

```bat
docker compose -f backend\docker-compose.yml up -d          # PostGIS on localhost:5432

cd backend
python -m venv .venv && .venv\Scripts\activate
python -m pip install -r requirements.txt
set DEMO_PASSWORD=Demo#2026                                  ^  required, your choice
python -m app.db.migrate upgrade
python -m app.seeding.seed_demo
uvicorn app.main:app --reload                               ^  http://localhost:8000/docs

cd ..\frontend
npm install
npm run dev                                                 ^  http://localhost:3000
```

All seeded accounts (investigator, analyst, admin) share the `DEMO_PASSWORD` you set. See
`backend/README.md` and `frontend/README.md` for every environment variable and default.

## Demo checklist

Journey: **LOGIN → DASHBOARD → ALERT → CASE → TRANSACTIONS → NETWORK → RUN PREDICTION →
EVIDENCE → GIS → INVESTIGATOR ACTION → AUDIT LOG → LOGOUT**

1. LOGIN — `a.patil@cic.gov.in` / your `DEMO_PASSWORD`. Cards and header show the seeded user.
2. DASHBOARD — KPIs (3 cases, current-run predictions, active alerts), risk map, recent alerts from
   the seed.
3. ALERT — open the alert generated for `TXN000000294`/`ATM00100`. Acknowledge it.
4. CASE — open `CASE-E2CAEBEA64`; add a note.
5. TRANSACTIONS — case tab shows the linked withdrawal history for `TXN000000294`.
6. NETWORK — entity/three-hop graph for the transaction, if available.
7. RUN PREDICTION — re-run the case prediction; prior prediction runs are preserved (history).
8. EVIDENCE — per-ATM evidence/factors for the top candidates.
9. GIS — heatmap of ranked ATM risk locations for the case.
10. INVESTIGATOR ACTION — change case status (`investigating` → `resolved`).
11. AUDIT LOG — log out, then log in as `admin@cic.gov.in`; every login/action above is listed.
12. LOGOUT — session is revoked server-side (re-auth required).

Data integrity: re-running a prediction supersedes the current run but never deletes history or
alerts. Severity bands: `low < 0.50`, `medium 0.50–0.70`, `high 0.70–0.90`, `critical ≥ 0.90`.

## Verification

| Check | Command (from `backend/`) |
|-------|---------------------------|
| Backend tests | `python -m pytest` |
| Lint | `.venv\Scripts\python -m ruff check app tests` |
| Smoke (auth → case → prediction → alerts → heatmap → analytics) | `set DEMO_PASSWORD=... && python scripts\smoke_test_api.py` |

| Check | Command (from `frontend/`) |
|-------|---------------------------|
| Lint / build | `npm run lint` / `npm run build` |

## Notes

- `backend/scripts/train_rf_baseline.py` and `docs/ml/` are intentionally left untracked; the
  committed model artifact `backend/ml/rf_baseline_model.joblib` is gitignored.