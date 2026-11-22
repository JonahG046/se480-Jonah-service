"""Lab 5: reproduce the known simultaneous-update failure.

Two requests read the same assignment before either saves.
Each request changes a different field, but the second save
can overwrite the first request's change.

The synchronization exists only in this test, not the API.
"""

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from app import store
from app.main import app

KNOWN_LIMIT = (
    "Concurrent updates can overwrite each other because the "
    "in-memory assignment store has no locking or version check."
)


@pytest.mark.xfail(strict=True, reason=KNOWN_LIMIT)
def test_concurrent_updates_preserve_both_changes(client, monkeypatch):
    """Known failure: two successful PATCH requests lose an update."""

    created = client.post(
        "/v1/assignments",
        json={
            "student_id": "stu_a7k92",
            "course_id": "crs_b8m21",
            "title": "Original Assignment",
            "due_at": "2026-11-25T23:59:00-06:00",
        },
    )

    assert created.status_code == 201

    assignment_id = created.json()["id"]
    path = f"/v1/assignments/{assignment_id}"

    # Both requests will reach this point after reading
    # the existing assignment but before saving updates.
    both_ready = threading.Barrier(2)
    original_clock = store.current_time

    def synchronize_before_save():
        try:
            both_ready.wait(timeout=4)
        except threading.BrokenBarrierError:
            # A future locking fix might serialize requests.
            pass

        return original_clock()

    monkeypatch.setattr(
        store,
        "current_time",
        synchronize_before_save,
    )

    def send_update(changes):
        with TestClient(
            app,
            raise_server_exceptions=False,
        ) as request_client:
            response = request_client.patch(
                path,
                json=changes,
            )
            return response.status_code

    # One request changes the title.
    # The other moves the assignment to another course.
    with ThreadPoolExecutor(max_workers=2) as executor:
        title_future = executor.submit(
            send_update,
            {"title": "Updated Assignment"},
        )
        course_future = executor.submit(
            send_update,
            {"course_id": "crs_c9n32"},
        )

        statuses = [
            title_future.result(timeout=12),
            course_future.result(timeout=12),
        ]

    final = store.ASSIGNMENTS[assignment_id]

    print("PATCH responses:", statuses)
    print("Final assignment title:", final.title)
    print("Final assignment course:", final.course_id)

    # Both requests report success.
    assert statuses == [200, 200]

    # A correct implementation would preserve BOTH changes.
    # The current implementation loses one of them.
    assert final.title == "Updated Assignment"
    assert final.course_id == "crs_c9n32"
