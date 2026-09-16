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

The SQLite application database is created automatically at:

```text
backend/data/sih_app.db
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

`GET /transactions/{transaction_id}`

### Create case

`POST /cases`

```json
{
  "transaction_id": "TXN000000294",
  "title": "Suspicious ATM withdrawal case",
  "description": "Prototype investigation case",
  "priority": "high"
}
```

### Run prediction and persist result

`POST /predictions/predict?case_id=CASE-...`

```json
{
  "transaction_id": "TXN000000294"
}
```

When `case_id` is supplied, the Top-5 predictions are stored and qualifying alerts are created automatically.

### Alerts

- `GET /alerts`
- `GET /alerts/{alert_id}`
- `PATCH /alerts/{alert_id}`

### Cases

- `GET /cases`
- `GET /cases/{case_id}`
- `PATCH /cases/{case_id}`

### Heatmap

`GET /heatmap`

For one case:

`GET /heatmap?case_id=CASE-...`

The heatmap endpoint returns prediction-derived ATM points. It does not claim that those points are confirmed real-world fraud locations.

### Analytics

- `GET /analytics`
- `GET /analytics/summary`

Analytics combine persisted prototype case/prediction/alert data with basic transaction/ATM dataset distributions.

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

This is a prototype. Before real deployment, add authentication/authorization, audit logging, rate limiting, encrypted transport, secrets management, PII minimization, access controls, structured logs and a production database such as PostgreSQL/PostGIS.
