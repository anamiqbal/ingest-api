"""
Standalone payload ingestion backend.

FastAPI + stdlib sqlite3. One job: accept a JSON payload, store it.

Run:  python3 -m uvicorn main:app --port 8010
Docs: http://127.0.0.1:8010/docs
"""

import json
import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI

# Configurable via env var (12-factor); defaults to a file next to this script
DB_PATH = Path(os.environ.get("DB_PATH", Path(__file__).parent / "data.db"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS payloads (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                received_at TEXT NOT NULL,
                body        TEXT NOT NULL
            )
            """
        )
    yield


app = FastAPI(title="Ingest API", version="1.0.0", lifespan=lifespan)


@app.post("/payloads", status_code=201)
async def ingest(
    payload: Any = Body(..., examples=[{"sensor": "temp-01", "value": 23.4}])
):
    """Accept any JSON body and persist it."""
    received_at = datetime.now(timezone.utc).isoformat()

    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute(
            "INSERT INTO payloads (received_at, body) VALUES (?, ?)",
            (received_at, json.dumps(payload)),
        )
        conn.commit()
        new_id = cur.lastrowid
    finally:
        conn.close()

    return {"id": new_id, "received_at": received_at, "body": payload}


@app.get("/payloads")
def list_payloads(limit: int = 50, offset: int = 0):
    """List stored payloads, newest first."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT * FROM payloads ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    finally:
        conn.close()

    return [
        {"id": r["id"], "received_at": r["received_at"], "body": json.loads(r["body"])}
        for r in rows
    ]


@app.get("/health")
def health():
    return {"status": "ok"}
