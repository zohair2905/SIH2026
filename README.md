# SIH26184 - Predictive Cybercrime Intelligence Platform

**Smart India Hackathon 2026**  
**Problem Statement:** Development of a Predictive Analytics Framework for Cybercrime Complaints to Forecast Likely Cash Withdrawal Locations in Advance, Enabling Generation of Actionable Intelligence for Timely and Proactive Cybercrime Intervention.

-----

##  Executive Summary

The **Predictive Cybercrime Intelligence Platform** is a decision-support system designed to assist law enforcement and financial investigators in forecasting likely cash-withdrawal hotspots (ATMs, service points) associated with cybercrime incidents before cash-out occurs.

By aggregating complaint data, transaction histories, spatial-temporal features, and entity networks, the platform generates calibrated risk scores, predictive time windows, and actionable explanations.

### Core Value Proposition

Transition from reactive post-incident investigation to **proactive intervention** by identifying where and when illicit funds are likely to be withdrawn, providing clear decision-support evidence within investigator workflows.

-----

##  Key Capabilities & Features

  - **Predictive ATM Cash-Out Risk:** Ranks top candidate withdrawal locations and predicts operational cash-out time windows.
  - **GIS Risk Heatmap & Drill-Down:** Interactive mapping showing critical, high, and medium-risk zones with location-level evidence.
  - **Mule Account Network Analysis:** Visualizes entity links, multi-hop transactions, and suspicious account clusters.
  - **Explainable Risk Scoring:** Discloses top contributing risk factors, transaction velocity, and historical pattern associations.
  - **Alert Management Lifecycle:** Threshold-based alert generation, assignment, acknowledgement, and resolution tracking.
  - **Security & Governance:** Role-Based Access Control (RBAC), sanitized data logging, PII masking, and full audit logging.

-----

##  Technology Stack

| Layer                  | Technology                                                      |
| :--------------------- | :-------------------------------------------------------------- |
| **Frontend**           | Next.js, TypeScript, Tailwind CSS, shadcn/ui                    |
| **GIS Mapping**        | MapLibre / Mapbox                                               |
| **Backend API**        | FastAPI (Python)                                                |
| **Database**           | PostgreSQL with PostGIS extension                               |
| **Machine Learning**   | Python, pandas, scikit-learn, Random Forest / Gradient Boosting |
| **Graph Analysis**     | NetworkX                                                        |
| **Cache & Workers**    | Redis + Celery / Background Workers                             |
| **Containerization**   | Docker & Docker Compose                                         |
| **CI/CD & Versioning** | GitHub Actions, Git                                             |

-----

##  System Architecture

``` 
+-------------------------------------------------------+
|                 Next.js Web App                       |
|               Dashboard / GIS / UI                    |
+-------------------------------------------------------+
                           | HTTPS / REST
                           v
+-------------------------------------------------------+
|                FastAPI Backend                        |
+-------------------------------------------------------+
         |                     |                  |
         v                     v                  v
+------------------+  +-----------------+  +------------------+

| PostgreSQL/PostGIS|  |   ML Service    |  | Alert/Job Worker |
+------------------+  +-----------------+  +------------------+

```

-----

##  Repository Structure

``` text
cybercrime-intelligence-platform/
├── frontend/             # Next.js web application & GIS interface
├── backend/              # FastAPI application services & API contracts
├── ml/                   # Model training, feature engineering, and inference pipelines
├── intelligence/        # Graph analysis and risk evaluation engine
├── data-pipeline/       # Synthetic data generation and ETL scripts
├── database/            # PostgreSQL schemas and PostGIS spatial scripts
├── infrastructure/      # Docker Compose & deployment configurations
└── docs/                # Architecture, API specifications, and design documents

```

-----

##  Quick Start & Development Setup

### Prerequisites

  - [Docker](https://www.docker.com/) & Docker Compose
  - [Node.js](https://nodejs.org/) (v18+)
  - [Python](https://www.python.org/) (v3.10+)

### 1\. Clone the Repository

``` bash
git clone https://github.com/zohair2905/SIH2026.git
cd SIH2026

```

### 2\. Run via Docker Compose

``` bash
docker-compose up --build

```

This spins up the frontend, backend, ML service, and PostGIS database services locally.

### 3\. Access Services

  - **Web Dashboard:** `http://localhost:3000`
  - **Backend API Docs:** `http://localhost:8000/docs`

-----

##  Core API Endpoints

| Method | Endpoint                  | Purpose                                       |
| :----- | :------------------------ | :-------------------------------------------- |
| `POST` | `/api/auth/login`         | User authentication & session generation      |
| `GET`  | `/api/dashboard`          | High-level metrics and active risk summary    |
| `GET`  | `/api/cases`              | List and filter active cybercrime cases       |
| `POST` | `/api/cases/{id}/predict` | Execute predictive risk model for a case      |
| `GET`  | `/api/cases/{id}/network` | Fetch graph/network links for linked entities |
| `GET`  | `/api/alerts`             | List priority alerts based on risk thresholds |

-----

##  Operational Disclaimer

This platform serves purely as **decision-support software**. Predictive scores, geographic hotspots, and time windows are probabilistic risk estimates intended to aid human investigators, and do not constitute autonomous legal action or definitive evidence.
