# SIH 26184 - Complete Backend Prototype

This backend wraps the existing Random Forest ATM candidate-ranking model with case management, persistent predictions, alerts, heatmap data and analytics APIs.

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

Run migrations and load the deterministic demo seed (3 cases, 5 predictions, 1 alert, 1 demo user):

```bat
python -m app.db.migrate upgrade
python -m app.seeding.seed_demo
```

## 3. Setup on Windows

```bat
cd /d "C:\Codes And Projects\SIH\SIH_26184_backend\backend"
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python scripts\preflight.py
python scripts\test_inference.py
```

## 3b. Development & testing

Copy `.env.example` to `.env` to override defaults (not required; sensible defaults exist). The API starts in degraded mode without the ML artifact so `/health` reports `model_loaded: false`; place the model at `ml/rf_baseline_model.joblib` to enable prediction.

Development & testing:

```bat
docker compose up -d
python -m app.db.migrate upgrade        # apply schema (tests auto-migrate sihdb_test)
python -m pip install -r requirements-dev.txt
python -m pytest                        # uses DATABASE_URL or sihdb_test on localhost
ruff check app tests
```

## 4. Start API

```bat
uvicorn app.main:app --reload
```

Open:

`http://127.0.0.1:8000/docs`

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

The pre-Phase-1 route layout (`/cases`, `/alerts`, `/heatmap`, `/analytics`, `/transactions/{id}`, `/predictions/predict`) remains available as thin aliases that delegate to the `/api/*` handlers; they are removed at the Phase 5 cutover.

## 6. End-to-end smoke test

After placing the model, start the server and run:

```bat
python scripts\smoke_test_api.py
```

It creates a case, runs prediction, persists results, creates alerts, checks heatmap data and reads analytics.

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

## 9. Security before deployment

This is a prototype. Before real deployment, add authentication/authorization, audit logging, rate limiting, encrypted transport, secrets management, PII minimization, access controls and structured logs.
