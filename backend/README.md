# SIH 26184 - Complete Backend Prototype

This backend wraps the existing Random Forest ATM candidate-ranking model with authentication (sessions + RBAC), audit logging, case management, persistent predictions, alerts, heatmap data and analytics APIs.

## 1. Important model contract

The backend uses the exact model saved by `train_rf_baseline.py`:

- `rf_baseline_model.joblib`
- RandomForestClassifier pipeline with preprocessing included
- 35 raw input features: 27 numerical + 8 categorical
- 5 pre-generated candidates per transaction
- candidate-level probability is ranked at transaction level

Do not replace the model with a separately retrained artifact unless the feature schema and training contract are kept identical.

## 2. Put files here

```text
backend/
  ml/rf_baseline_model.joblib          # copy your 449 MB model here
  data/transactions.csv
  data/atm_master.csv
  data/transaction_atm_candidates.csv
```

The application database is PostgreSQL with PostGIS, provided by `docker-compose.yml`:

```text
docker compose up -d        # runs sih_postgis on localhost:5432 (sih/sih@/sihdb)
```

Run migrations and load the deterministic demo seed (3 cases, 5 predictions, 1 alert, 3 users):

```bat
set DEMO_PASSWORD=SomeStrongPassword
python -m app.db.migrate upgrade
python -m app.seeding.seed_demo
```

`DEMO_PASSWORD` is **required** — it is the password for every seeded demo account where there is no
hardcoded default. The three seeded roles (all use the same `DEMO_PASSWORD`):

| Role | Email | Visibility |
|------|-------|------------|
| Investigator | `a.patil@cic.gov.in` | standard investigator workflow |
| Analyst | `analyst@cic.gov.in` | read-only |
| Admin | `admin@cic.gov.in` | Audit Logs (admin-only) |

## 3. Setup on Windows

```bat
cd backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
set DEMO_PASSWORD=SomeStrongPassword
python scripts\preflight.py
python scripts\test_inference.py
```

## 3b. Development & testing

Environment variables are read from the process environment (there is no `.env` loader). Set
`DATABASE_URL`, `DEMO_PASSWORD`, `CORS_ORIGINS`, `ACCESS_TOKEN_TTL_HOURS`, `SESSION_COOKIE_NAME` and
`AUTH_COOKIE_SECURE` as needed; see `.env.example` for every variable and its default. The API starts
in degraded mode without the ML artifact so `/health` reports `model_loaded: false`; place the model
at `ml/rf_baseline_model.joblib` to enable prediction.

```bat
docker compose up -d
set DEMO_PASSWORD=SomeStrongPassword
python -m app.db.migrate upgrade        # apply schema (tests auto-migrate sihdb_test)
python -m pip install -r requirements-dev.txt
python -m pytest                        # uses DATABASE_URL or sihdb_test on localhost
ruff check app tests
```

## 4. Start API

```bat
set DEMO_PASSWORD=SomeStrongPassword
uvicorn app.main:app --reload
```

Open:

`http://127.0.0.1:8000/docs`

## 4b. Authentication

Every route except `/health`, `/docs`, `/redoc`, `/openapi.json`, `POST /api/auth/login`
and `POST /api/auth/logout` requires a valid session (see `app/core/middleware.py`):

- `POST /api/auth/login` — body `{email, password}`. Returns `{access_token, token_type, user}`
  and sets an httpOnly cookie.
- `GET /api/auth/me` — current session's user.
- `POST /api/auth/logout` — revokes the session.
- Sessions are opaque random tokens stored as SHA-256 digests; passwords are stored
  PCI-style hashed (scrypt + constant-time verify).
- RBAC: `analyst` = read-only; `investigator`/`admin` = operator actions (cases, alerts,
  predictions); `admin` only = the Audit Logs endpoint.
- Every login/logout/operator action is written to the audit log (no secrets, no tokens).

## 5. Core API flow

### Health

`GET /health`

### Transaction

`GET /api/transactions/{transaction_id}`

### Create case

`POST /api/cases`

```json
{
  "transaction_id": "TXN000000294",
  "title": "Suspicious ATM withdrawal case",
  "description": "Prototype investigation case",
  "priority": "high"
}
```

### Run prediction and persist result

`POST /api/predictions/predict?case_id=CASE-...`

```json
{
  "transaction_id": "TXN000000294"
}
```

When `case_id` is supplied, the Top-5 predictions are stored and qualifying alerts are created automatically. Re-prediction replaces the stored Top-5 but **appends** new alerts; prior alerts are never deleted.

### Alerts

- `GET /api/alerts`
- `GET /api/alerts/{alert_id}`
- `PATCH /api/alerts/{alert_id}`
- `POST /api/alerts/{alert_id}/acknowledge`

### Cases

- `GET /api/cases`
- `GET /api/cases/{case_id}`
- `PATCH /api/cases/{case_id}`
- `GET /api/cases/{case_id}/transactions`

### Heatmap

`GET /api/heatmap`

For one case:

`GET /api/heatmap?case_id=CASE-...`

The heatmap endpoint returns prediction-derived ATM points. It does not claim that those points are confirmed real-world fraud locations.

### Analytics

- `GET /api/analytics`
- `GET /api/analytics/summary`

Analytics combine persisted prototype case/prediction/alert data with basic transaction/ATM dataset distributions.

The pre-Phase-1 route layout (`/cases`, `/alerts`, `/heatmap`, `/analytics`, `/transactions/{id}`, `/predictions/predict`) remains available as thin auth-gated aliases that delegate to the `/api/*` handlers for backward compatibility; prefer the `/api/*` routes.

## 6. End-to-end smoke test

After placing the model and seeding with a `DEMO_PASSWORD`, run:

```bat
set DEMO_PASSWORD=SomeStrongPassword
python scripts\smoke_test_api.py
```

It logs in as the seeded investigator, then exercises auth, case creation, prediction
persistence, alerts, heatmap data and analytics.

## 7. Architecture

```text
Frontend / Investigator UI
          |
       FastAPI
          |
  +-------+---------+----------------+
  |       |         |                |
Cases  Prediction  Alerts         Analytics
          |
     Feature Service
          |
     Candidate Set
          |
  rf_baseline_model.joblib
          |
       Top-5 ATM ranking
          |
   Prediction persistence
          |
      Heatmap / Alerts
```

## 8. Important prototype limitation

The current public/sanitized benchmark contains a pre-generated five-candidate set for the 10,000 benchmark transactions. The backend reuses those candidates exactly so inference is consistent with the trained baseline.

It does **not** invent a new candidate-generation algorithm for arbitrary unseen transactions. For production deployment, replace `CandidateService` with the authorized candidate-generation logic used to build training data, backed by real bank/ATM telemetry.

The dataset/model materials also identify the benchmark as controlled synthetic and not validated as real-world ATM-location prediction. Do not present model scores as guaranteed future withdrawal probabilities.

## 9. Security status

Authentication, RBAC, audit logging and request-id tracing are implemented and covered by tests
(`tests/test_auth_security.py`, `app/core/middleware.py`, `app/core/security.py`).

Remaining hardening before real deployment: rate limiting / account lockout on login, encrypted
transport (TLS), secrets management, PII minimization controls and structured-log centralization.
