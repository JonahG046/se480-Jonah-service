"""Tests for unexpected and framework-generated API errors."""

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import store
from app.main import app


def test_unexpected_error_returns_safe_problem(monkeypatch):
    """Unexpected exceptions return 500 without leaking internal details."""

    class BrokenStudents:
        def values(self):
            raise RuntimeError("PRIVATE_INTERNAL_ERROR_DETAILS")

    monkeypatch.setattr(store, "STUDENTS", BrokenStudents())

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/v1/students")

    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/problem+json")

    body = response.json()
    assert body["type"] == "about:blank"
    assert body["status"] == 500
    assert body["title"] == "Something went wrong"
    assert body["instance"] == "/v1/students"
    assert "PRIVATE_INTERNAL_ERROR_DETAILS" not in response.text


def test_other_http_error_uses_problem_details(monkeypatch):
    """Coverage finding: exercise the generic framework HTTP error branch."""

    class UnavailableStudents:
        def values(self):
            raise HTTPException(
                status_code=503,
                detail="Student records are temporarily unavailable.",
            )

    monkeypatch.setattr(store, "STUDENTS", UnavailableStudents())

    with TestClient(app) as client:
        response = client.get("/v1/students")

    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")

    body = response.json()
    assert body["type"] == "about:blank"
    assert body["status"] == 503
    assert body["instance"] == "/v1/students"
