"""Tests for the payload ingest API."""

import os
import tempfile

# Point the app at a temp database BEFORE importing it
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")

from fastapi.testclient import TestClient

from main import app


def get_client() -> TestClient:
    # Context manager triggers the lifespan (creates the table)
    return TestClient(app)


def test_health():
    with get_client() as client:
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


def test_ingest_object_payload():
    with get_client() as client:
        r = client.post("/payloads", json={"sensor": "temp-01", "value": 23.4})
        assert r.status_code == 201
        data = r.json()
        assert data["body"] == {"sensor": "temp-01", "value": 23.4}
        assert "id" in data and "received_at" in data


def test_ingest_array_payload():
    with get_client() as client:
        r = client.post("/payloads", json=[1, 2, 3])
        assert r.status_code == 201
        assert r.json()["body"] == [1, 2, 3]


def test_invalid_json_rejected():
    with get_client() as client:
        r = client.post(
            "/payloads",
            content="not json",
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == 422


def test_list_payloads_newest_first():
    with get_client() as client:
        first = client.post("/payloads", json={"n": 1}).json()["id"]
        second = client.post("/payloads", json={"n": 2}).json()["id"]

        r = client.get("/payloads")
        assert r.status_code == 200
        ids = [row["id"] for row in r.json()]
        assert ids.index(second) < ids.index(first)  # newest first


def test_pagination():
    with get_client() as client:
        for i in range(5):
            client.post("/payloads", json={"i": i})
        r = client.get("/payloads", params={"limit": 2})
        assert len(r.json()) == 2
