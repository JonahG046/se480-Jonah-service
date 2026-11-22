"""Lab 5 tests for request logging, request IDs, and metrics."""

import json
import re

import pytest
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from app import observability, store
from app.main import app

FIELDS = [
    "ts",
    "level",
    "request_id",
    "method",
    "route",
    "status",
    "duration_ms",
]


def logged(capsys):
    """Read JSON request lines written to standard output."""
    output = capsys.readouterr().out
    return [json.loads(line) for line in output.splitlines() if line.startswith("{")]


def counted(route, status):
    """Read one request-counter value."""
    return (
        REGISTRY.get_sample_value(
            "http_requests_total",
            {"route": route, "status": status},
        )
        or 0.0
    )


def test_one_json_line_per_request(client, capsys):
    """A successful request produces exactly one structured line."""
    capsys.readouterr()

    response = client.get("/v1/students")
    lines = logged(capsys)

    assert response.status_code == 200
    assert len(lines) == 1

    line = lines[0]

    assert list(line) == FIELDS
    assert line["level"] == "INFO"
    assert line["method"] == "GET"
    assert line["route"] == "/v1/students"
    assert line["status"] == 200
    assert isinstance(line["duration_ms"], int)
    assert line["duration_ms"] >= 0
    assert line["request_id"] == response.headers["X-Request-ID"]


def test_404_logs_route_template_not_assignment_id(client, capsys):
    """Private assignment IDs must not appear in request logs."""
    private_id = "asg_private_assignment_123456"
    capsys.readouterr()

    response = client.get(f"/v1/assignments/{private_id}")
    lines = logged(capsys)

    assert response.status_code == 404
    assert len(lines) == 1
    assert lines[0]["route"] == "/v1/assignments/{assignment_id}"
    assert lines[0]["status"] == 404
    assert lines[0]["request_id"] == response.headers["X-Request-ID"]

    assert private_id not in json.dumps(lines)


def test_unknown_path_uses_fixed_label(client, capsys):
    """An unmatched path must not be copied into logs."""
    capsys.readouterr()

    response = client.get("/v1/private/secret-value-123")
    lines = logged(capsys)

    assert response.status_code == 404
    assert len(lines) == 1
    assert lines[0]["route"] == "unmatched"
    assert "secret-value-123" not in json.dumps(lines)


def test_500_has_matching_request_id_and_log(monkeypatch, capsys):
    """Unexpected errors retain their request ID and safe response."""

    class BrokenStudents:
        def values(self):
            raise RuntimeError("PRIVATE_INTERNAL_ERROR_DETAILS")

    monkeypatch.setattr(store, "STUDENTS", BrokenStudents())

    capsys.readouterr()

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/v1/students")

    lines = logged(capsys)

    assert response.status_code == 500
    assert len(lines) == 1
    assert lines[0]["level"] == "ERROR"
    assert lines[0]["status"] == 500
    assert lines[0]["route"] == "/v1/students"
    assert lines[0]["request_id"] == response.headers["X-Request-ID"]
    assert "PRIVATE_INTERNAL_ERROR_DETAILS" not in response.text


def test_incoming_request_id_is_validated(client):
    """Accept safe request IDs and replace unsafe values."""
    safe_id = "student-request-12345"

    accepted = client.get(
        "/v1/students",
        headers={"X-Request-ID": safe_id},
    )
    assert accepted.headers["X-Request-ID"] == safe_id

    rejected = client.get(
        "/v1/students",
        headers={"X-Request-ID": 'x","level":"FAKE'},
    )

    assert re.fullmatch(
        r"[0-9a-f]{16}",
        rejected.headers["X-Request-ID"],
    )


def test_request_log_contains_no_student_information(client, capsys):
    """Student names and emails belong in responses, not logs."""
    capsys.readouterr()

    response = client.get("/v1/students")
    lines = logged(capsys)

    assert response.status_code == 200
    assert len(lines) == 1

    line_text = json.dumps(lines)

    assert "Alex Johnson" not in line_text
    assert "Jordan Lee" not in line_text
    assert "alex@example.edu" not in line_text
    assert "Authorization" not in line_text


def test_health_and_metrics_are_not_logged_or_counted(client, capsys):
    """Operational requests should not inflate user traffic."""
    before = counted("/health", "2xx")
    capsys.readouterr()

    health = client.get("/health")
    metrics = client.get("/metrics")

    assert health.status_code == 200
    assert metrics.status_code == 200
    assert logged(capsys) == []
    assert counted("/health", "2xx") == before


def test_successful_request_increases_counter(client):
    """The Prometheus counter increases after a real request."""
    route = "/v1/students"
    before = counted(route, "2xx")

    response = client.get(route)

    assert response.status_code == 200
    assert counted(route, "2xx") == before + 1


def test_deadline_conflict_increases_business_counter(client):
    """A rejected completed-assignment deadline updates our metric."""
    before = REGISTRY.get_sample_value("assignment_deadline_conflicts_total") or 0.0

    created = client.post(
        "/v1/assignments",
        json={
            "student_id": "stu_a7k92",
            "course_id": "crs_b8m21",
            "title": "Database Design Project",
            "due_at": "2026-11-15T23:59:00-06:00",
        },
    )

    assert created.status_code == 201

    path = f"/v1/assignments/{created.json()['id']}"

    completed = client.patch(
        path,
        json={"status": "completed"},
    )
    assert completed.status_code == 200

    blocked = client.patch(
        path,
        json={"due_at": "2026-11-20T23:59:00-06:00"},
    )
    assert blocked.status_code == 409

    after = REGISTRY.get_sample_value("assignment_deadline_conflicts_total")

    assert after == before + 1


def test_metrics_uses_prometheus_format(client):
    """Metrics include request, duration, and business counters."""
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "http_requests_total" in response.text
    assert "http_request_duration_seconds_bucket" in response.text
    assert "assignment_deadline_conflicts_total" in response.text


def test_reversible_startup_failure(monkeypatch):
    """The deployment failure switch works only when enabled."""
    monkeypatch.delenv("LAB5_FAIL_STARTUP", raising=False)
    observability.fail_startup_if_asked()

    monkeypatch.setenv("LAB5_FAIL_STARTUP", "1")

    with pytest.raises(SystemExit):
        observability.fail_startup_if_asked()
