"""Smoke test the FastAPI app boots and serves health."""

from fastapi.testclient import TestClient

from stackhealth.api.main import app


def test_root() -> None:
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["name"] == "stackhealth-api"


def test_health() -> None:
    client = TestClient(app)
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
