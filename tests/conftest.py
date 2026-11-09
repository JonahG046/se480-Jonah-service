
"""Shared fixtures for Student Assignment Tracker tests."""

import pytest
from fastapi.testclient import TestClient

from app import store
from app.main import app


@pytest.fixture
def client():
    """Provide a clean application client for each test."""

    store.reset()

    with TestClient(app) as test_client:
        yield test_client

    store.reset()
