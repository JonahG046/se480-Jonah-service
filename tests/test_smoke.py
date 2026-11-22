"""Smoke tests for the Student Assignment Tracker."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    """Health reports status and operational information."""

    response = client.get("/health")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"
    assert body["started_at"]
    assert body["uptime_seconds"] >= 0
    assert body["commit"]
    assert set(body["store"]) == {
        "students",
        "courses",
        "assignments",
    }


def test_metrics():
    """Metrics are available in Prometheus format."""

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "http_requests_total" in response.text
    assert "http_request_duration_seconds" in response.text


def test_operational_routes_excluded_from_schema():
    """Health and metrics are not public API operations."""

    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/health" not in paths
    assert "/metrics" not in paths
