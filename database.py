"""
Database module for Taiwan Weather Forecast.
Handles SQLite connection, schema creation, upsert operations, and verification queries.
"""

import os
import sqlite3
import pandas as pd
import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS TemperatureForecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    regionName TEXT NOT NULL,
    dataDate   TEXT NOT NULL,
    minT REAL,
    maxT REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(regionName, dataDate)
);
"""

def get_conn() -> sqlite3.Connection:
    """Return a connection to the SQLite database, creating parent dirs if needed."""
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    return sqlite3.connect(config.DB_PATH)

def init_db():
    """Initialize database tables according to schema."""
    with get_conn() as conn:
        conn.execute(SCHEMA)

def upsert(df: pd.DataFrame):
    """
    Upsert weather forecast records into TemperatureForecasts table.
    Uses ON CONFLICT DO UPDATE to prevent duplicate rows.
    """
    if df.empty:
        return
    sql = """
    INSERT INTO TemperatureForecasts (regionName, dataDate, minT, maxT)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(regionName, dataDate)
    DO UPDATE SET minT = excluded.minT,
                  maxT = excluded.maxT,
                  created_at = CURRENT_TIMESTAMP;
    """
    records = df[["regionName", "dataDate", "minT", "maxT"]].itertuples(index=False, name=None)
    with get_conn() as conn:
        conn.executemany(sql, list(records))

def prune_past_dates(today: str) -> int:
    """
    Delete forecasts for dates before today.

    Upsert only inserts and updates, so without this the table keeps
    accumulating expired dates and the dashboard shows yesterday's forecast
    alongside the current week. Returns the number of rows removed.
    """
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM TemperatureForecasts WHERE dataDate < ?", (today,))
        return cur.rowcount

def verify_data() -> dict:
    """
    Run verification SQL queries as specified in Step 10 of workflow.md.
    Returns a dict with query results for validation.
    """
    with get_conn() as conn:
        # 1. 所有地區
        regions = [r[0] for r in conn.execute(
            "SELECT DISTINCT regionName FROM TemperatureForecasts ORDER BY regionName"
        ).fetchall()]

        # 2. 中部地區或第一地區一週氣溫
        sample_region = "中部地區" if "中部地區" in regions else (regions[0] if regions else "")
        sample_forecast = conn.execute(
            "SELECT dataDate, minT, maxT FROM TemperatureForecasts WHERE regionName = ? ORDER BY dataDate",
            (sample_region,)
        ).fetchall()

        # 3. 每個地區的天數
        counts = dict(conn.execute(
            "SELECT regionName, COUNT(*) AS days FROM TemperatureForecasts GROUP BY regionName"
        ).fetchall())

        # 4. 異常資料 (應為 0)
        anomalies = conn.execute(
            "SELECT * FROM TemperatureForecasts WHERE minT IS NULL OR maxT IS NULL OR minT > maxT"
        ).fetchall()

        total_rows = conn.execute("SELECT COUNT(*) FROM TemperatureForecasts").fetchone()[0]

    return {
        "regions": regions,
        "sample_region": sample_region,
        "sample_forecast": sample_forecast,
        "days_per_region": counts,
        "anomalies_count": len(anomalies),
        "total_rows": total_rows,
    }

if __name__ == "__main__":
    init_db()
    print("Database initialized at:", config.DB_PATH)
    results = verify_data()
    print("Current DB status:", results)
