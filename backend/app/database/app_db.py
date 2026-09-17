from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.config import BASE_DIR

DB_FILE = BASE_DIR / "data" / "sih_app.db"


class AppDB:
    """Small SQLite persistence layer for cases, predictions and alerts."""

    def __init__(self, db_file: Path = DB_FILE) -> None:
        self.db_file = Path(db_file)
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS cases (
                    case_id TEXT PRIMARY KEY,
                    transaction_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL DEFAULT 'open',
                    priority TEXT NOT NULL DEFAULT 'medium',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS predictions (
                    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id TEXT NOT NULL,
                    transaction_id TEXT NOT NULL,
                    atm_id TEXT NOT NULL,
                    rank INTEGER NOT NULL,
                    risk_score REAL NOT NULL,
                    candidate_rank INTEGER NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    city TEXT,
                    area_type TEXT,
                    atm_status TEXT,
                    atm_density_1km REAL,
                    atm_withdrawal_count REAL,
                    atm_recent_activity REAL,
                    synthetic_location_data INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(case_id) REFERENCES cases(case_id)
                );

                CREATE TABLE IF NOT EXISTS alerts (
                    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id TEXT NOT NULL,
                    transaction_id TEXT NOT NULL,
                    atm_id TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    severity TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'new',
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(case_id) REFERENCES cases(case_id)
                );

                CREATE INDEX IF NOT EXISTS idx_cases_transaction ON cases(transaction_id);
                CREATE INDEX IF NOT EXISTS idx_predictions_case ON predictions(case_id);
                CREATE INDEX IF NOT EXISTS idx_predictions_atm ON predictions(atm_id);
                CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
                CREATE INDEX IF NOT EXISTS idx_alerts_case ON alerts(case_id);
                """
            )

    @staticmethod
    def now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def create_case(
        self,
        case_id: str,
        transaction_id: str,
        title: str,
        description: str | None,
        priority: str,
    ) -> dict[str, Any]:
        now = self.now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO cases(case_id, transaction_id, title, description, status, priority, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'open', ?, ?, ?)
                """,
                (case_id, transaction_id, title, description, priority, now, now),
            )
        return self.get_case(case_id)  # type: ignore[return-value]

    def get_case(self, case_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,)).fetchone()
            return dict(row) if row else None

    def list_cases(self, status: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM cases"
        params: tuple[Any, ...] = ()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY created_at DESC"
        with self.connect() as conn:
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    def update_case_status(self, case_id: str, status: str) -> dict[str, Any] | None:
        now = self.now()
        with self.connect() as conn:
            conn.execute("UPDATE cases SET status = ?, updated_at = ? WHERE case_id = ?", (status, now, case_id))
        return self.get_case(case_id)

    def save_predictions(self, case_id: str, transaction_id: str, predictions: list[dict[str, Any]]) -> None:
        now = self.now()
        with self.connect() as conn:
            conn.execute("DELETE FROM predictions WHERE case_id = ?", (case_id,))
            conn.executemany(
                """
                INSERT INTO predictions(
                    case_id, transaction_id, atm_id, rank, risk_score, candidate_rank,
                    latitude, longitude, city, area_type, atm_status, atm_density_1km,
                    atm_withdrawal_count, atm_recent_activity, synthetic_location_data, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        case_id, transaction_id, p["atm_id"], p["rank"], p["risk_score"],
                        p["candidate_rank"], p.get("latitude"), p.get("longitude"), p.get("city"),
                        p.get("area_type"), p.get("atm_status"), p.get("atm_density_1km"),
                        p.get("atm_withdrawal_count"), p.get("atm_recent_activity"),
                        int(bool(p.get("synthetic_location_data", True))), now,
                    )
                    for p in predictions
                ],
            )

    def get_predictions(self, case_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT * FROM predictions WHERE case_id = ? ORDER BY rank", (case_id,)
            ).fetchall()]

    def create_alerts(self, case_id: str, transaction_id: str, predictions: list[dict[str, Any]], threshold: float) -> list[dict[str, Any]]:
        now = self.now()
        created = []
        with self.connect() as conn:
            conn.execute("DELETE FROM alerts WHERE case_id = ? AND status = 'new'", (case_id,))
            for p in predictions:
                score = float(p["risk_score"])
                if score < threshold:
                    continue
                severity = "critical" if score >= 0.90 else "high" if score >= 0.70 else "medium"
                message = f"{severity.upper()} ATM risk for {p['atm_id']} with model score {score:.2%}."
                cur = conn.execute(
                    """
                    INSERT INTO alerts(case_id, transaction_id, atm_id, risk_score, severity, status, message, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, 'new', ?, ?, ?)
                    """,
                    (case_id, transaction_id, p["atm_id"], score, severity, message, now, now),
                )
                created.append(self.get_alert(int(cur.lastrowid)))
        return [a for a in created if a is not None]

    def get_alert(self, alert_id: int) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM alerts WHERE alert_id = ?", (alert_id,)).fetchone()
            return dict(row) if row else None

    def list_alerts(self, status: str | None = None, severity: str | None = None) -> list[dict[str, Any]]:
        clauses = []
        params: list[Any] = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        if severity:
            clauses.append("severity = ?")
            params.append(severity)
        query = "SELECT * FROM alerts"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY risk_score DESC, created_at DESC"
        with self.connect() as conn:
            return [dict(r) for r in conn.execute(query, tuple(params)).fetchall()]

    def update_alert_status(self, alert_id: int, status: str) -> dict[str, Any] | None:
        now = self.now()
        with self.connect() as conn:
            conn.execute("UPDATE alerts SET status = ?, updated_at = ? WHERE alert_id = ?", (status, now, alert_id))
        return self.get_alert(alert_id)

    def analytics_summary(self) -> dict[str, Any]:
        with self.connect() as conn:
            cases = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
            open_cases = conn.execute("SELECT COUNT(*) FROM cases WHERE status = 'open'").fetchone()[0]
            alerts = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
            active_alerts = conn.execute("SELECT COUNT(*) FROM alerts WHERE status IN ('new','acknowledged')").fetchone()[0]
            predictions = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
            avg_risk = conn.execute("SELECT AVG(risk_score) FROM predictions").fetchone()[0]
        return {
            "cases": int(cases),
            "open_cases": int(open_cases),
            "alerts": int(alerts),
            "active_alerts": int(active_alerts),
            "predictions": int(predictions),
            "average_prediction_risk": float(avg_risk) if avg_risk is not None else None,
        }

    def prediction_heatmap(self, case_id: str | None = None) -> list[dict[str, Any]]:
        query = """
            SELECT atm_id, latitude, longitude, MAX(risk_score) AS risk_score,
                   MIN(rank) AS best_rank, COUNT(*) AS observation_count
            FROM predictions
        """
        params: tuple[Any, ...] = ()
        if case_id:
            query += " WHERE case_id = ?"
            params = (case_id,)
        query += " GROUP BY atm_id, latitude, longitude ORDER BY risk_score DESC"
        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


_db: AppDB | None = None


def get_app_db() -> AppDB:
    global _db
    if _db is None:
        _db = AppDB()
    return _db
