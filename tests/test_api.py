
"""Unit tests for the Student Assignment Tracker API."""

from fastapi.testclient import TestClient


VALID_ASSIGNMENT = {
    "student_id": "stu_a7k92",
    "course_id": "crs_b8m21",
    "title": "Database Design Project",
    "due_at": "2026-11-15T23:59:00-06:00",
}


def create_assignment(client: TestClient, **changes):
    """Create an assignment using valid sample data."""

    body = {**VALID_ASSIGNMENT, **changes}

    return client.post("/v1/assignments", json=body)


def assert_problem(response, status: int, slug: str):
    """Verify status, content type, and ProblemDetails body."""

    assert response.status_code == status

    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    body = response.json()

    assert body["status"] == status
    assert body["type"].endswith("/" + slug)
    assert body["title"]
    assert body["detail"]
    assert body["instance"] == response.request.url.path

    return body


# ---------------------------------------------------------
# Read-only resources
# ---------------------------------------------------------

def test_list_students(client):
    response = client.get("/v1/students")

    assert response.status_code == 200

    students = response.json()

    assert len(students) == 2
    assert students[0]["id"] == "stu_a7k92"
    assert "name" in students[0]
    assert "email" in students[0]


def test_list_courses(client):
    response = client.get("/v1/courses")

    assert response.status_code == 200

    courses = response.json()

    assert len(courses) == 2
    assert courses[0]["code"] == "SE480"
    assert "name" in courses[0]


# ---------------------------------------------------------
# GET /assignments
# ---------------------------------------------------------

def test_list_assignments_empty(client):
    response = client.get("/v1/assignments")

    assert response.status_code == 200
    assert response.json() == []


def test_list_assignments_by_student(client):
    created = create_assignment(client)

    assert created.status_code == 201

    response = client.get(
        "/v1/assignments",
        params={"student_id": "stu_a7k92"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1

    other = client.get(
        "/v1/assignments",
        params={"student_id": "stu_b8m21"},
    )

    assert other.status_code == 200
    assert other.json() == []


def test_list_assignments_unknown_student(client):
    response = client.get(
        "/v1/assignments",
        params={"student_id": "stu_unknown"},
    )

    assert_problem(response, 404, "not-found")


def test_list_assignments_invalid_filter(client):
    response = client.get("/v1/assignments?student_id=")

    body = assert_problem(
        response,
        422,
        "validation-failed",
    )

    assert len(body["errors"]) >= 1


# ---------------------------------------------------------
# POST /assignments
# ---------------------------------------------------------

def test_create_assignment(client):
    response = create_assignment(client)

    assert response.status_code == 201

    body = response.json()

    assert body["id"].startswith("asg_")
    assert body["student_id"] == "stu_a7k92"
    assert body["course_id"] == "crs_b8m21"
    assert body["title"] == "Database Design Project"
    assert body["status"] == "pending"
    assert "updated_at" in body

    assert response.headers["Location"] == (
        f"/v1/assignments/{body['id']}"
    )


def test_create_assignment_rejects_numeric_deadline(client):
    """Reject Unix timestamps that violate our date-time schema."""

    response = create_assignment(client, due_at=0)

    problem = assert_problem(
        response,
        422,
        "validation-failed",
    )

    assert any(
        error["field"] == "due_at"
        for error in problem["errors"]
    )


def test_create_assignment_missing_title(client):
    body = VALID_ASSIGNMENT.copy()
    del body["title"]

    response = client.post("/v1/assignments", json=body)

    problem = assert_problem(
        response,
        422,
        "validation-failed",
    )

    assert any(
        error["field"] == "title"
        for error in problem["errors"]
    )


def test_create_assignment_without_timezone(client):
    response = create_assignment(
        client,
        due_at="2026-11-15T23:59:00",
    )

    problem = assert_problem(
        response,
        422,
        "validation-failed",
    )

    assert any(
        error["field"] == "due_at"
        for error in problem["errors"]
    )


def test_create_assignment_unknown_student(client):
    response = create_assignment(
        client,
        student_id="stu_unknown",
    )

    assert_problem(response, 404, "not-found")


def test_create_assignment_unknown_course(client):
    response = create_assignment(
        client,
        course_id="crs_unknown",
    )

    assert_problem(response, 404, "not-found")


# ---------------------------------------------------------
# GET /assignments/{assignment_id}
# ---------------------------------------------------------

def test_get_assignment(client):
    created = create_assignment(client)
    assignment_id = created.json()["id"]

    response = client.get(
        f"/v1/assignments/{assignment_id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == assignment_id
    assert response.json()["status"] == "pending"


def test_get_unknown_assignment(client):
    response = client.get(
        "/v1/assignments/asg_unknown"
    )

    assert_problem(response, 404, "not-found")


# ---------------------------------------------------------
# PATCH /assignments/{assignment_id}
# ---------------------------------------------------------

def test_update_assignment(client):
    created = create_assignment(client)
    assignment_id = created.json()["id"]

    response = client.patch(
        f"/v1/assignments/{assignment_id}",
        json={
            "title": "Updated Database Project",
            "course_id": "crs_c9n32",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["title"] == "Updated Database Project"
    assert body["course_id"] == "crs_c9n32"
    assert body["student_id"] == "stu_a7k92"


def test_mark_assignment_completed(client):
    created = create_assignment(client)
    assignment_id = created.json()["id"]

    response = client.patch(
        f"/v1/assignments/{assignment_id}",
        json={"status": "completed"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_completed_deadline_conflict(client):
    created = create_assignment(client)
    assignment_id = created.json()["id"]

    path = f"/v1/assignments/{assignment_id}"

    completed = client.patch(
        path,
        json={"status": "completed"},
    )

    assert completed.status_code == 200

    response = client.patch(
        path,
        json={
            "due_at": "2026-11-20T23:59:00-06:00"
        },
    )

    assert_problem(
        response,
        409,
        "completed-assignment",
    )


def test_reopen_before_changing_deadline(client):
    created = create_assignment(client)
    assignment_id = created.json()["id"]

    path = f"/v1/assignments/{assignment_id}"

    assert client.patch(
        path,
        json={"status": "completed"},
    ).status_code == 200

    # Reopening and changing the deadline in one PATCH
    # must still be rejected.
    blocked = client.patch(
        path,
        json={
            "status": "pending",
            "due_at": "2026-11-20T23:59:00-06:00",
        },
    )

    assert_problem(
        blocked,
        409,
        "completed-assignment",
    )

    # Reopen the assignment first.
    reopened = client.patch(
        path,
        json={"status": "pending"},
    )

    assert reopened.status_code == 200

    # Then change the deadline in a separate request.
    changed = client.patch(
        path,
        json={
            "due_at": "2026-11-20T23:59:00-06:00"
        },
    )

    assert changed.status_code == 200

    assert changed.json()["due_at"] == (
        "2026-11-20T23:59:00-06:00"
    )


def test_update_unknown_assignment(client):
    response = client.patch(
        "/v1/assignments/asg_unknown",
        json={"title": "Updated Title"},
    )

    assert_problem(response, 404, "not-found")


def test_update_unknown_course(client):
    created = create_assignment(client)
    assignment_id = created.json()["id"]

    response = client.patch(
        f"/v1/assignments/{assignment_id}",
        json={"course_id": "crs_unknown"},
    )

    assert_problem(response, 404, "not-found")


def test_update_cannot_change_student(client):
    created = create_assignment(client)
    assignment_id = created.json()["id"]

    response = client.patch(
        f"/v1/assignments/{assignment_id}",
        json={"student_id": "stu_b8m21"},
    )

    assert_problem(
        response,
        422,
        "validation-failed",
    )


def test_update_requires_field(client):
    created = create_assignment(client)
    assignment_id = created.json()["id"]

    response = client.patch(
        f"/v1/assignments/{assignment_id}",
        json={},
    )

    assert_problem(
        response,
        422,
        "validation-failed",
    )


# ---------------------------------------------------------
# DELETE /assignments/{assignment_id}
# ---------------------------------------------------------

def test_delete_assignment(client):
    created = create_assignment(client)
    assignment_id = created.json()["id"]

    path = f"/v1/assignments/{assignment_id}"

    response = client.delete(path)

    assert response.status_code == 204
    assert response.content == b""

    missing = client.get(path)

    assert_problem(missing, 404, "not-found")


def test_delete_unknown_assignment(client):
    response = client.delete(
        "/v1/assignments/asg_unknown"
    )

    assert_problem(response, 404, "not-found")


# ---------------------------------------------------------
# Shared HTTP error handling
# ---------------------------------------------------------

def test_unknown_path_returns_problem_details(client):
    response = client.get("/v1/does-not-exist")

    assert_problem(response, 404, "not-found")


def test_unsupported_method_has_allow_header(client):
    response = client.put("/v1/assignments")

    assert response.status_code == 405

    assert response.headers["content-type"].startswith(
        "application/problem+json"
    )

    allowed = {
        method.strip()
        for method in response.headers["Allow"].split(",")
    }

    assert {"GET", "POST"}.issubset(allowed)
    assert response.json()["status"] == 405


# ---------------------------------------------------------
# Regression tests for Schemathesis findings
# ---------------------------------------------------------

def test_create_assignment_rejects_malformed_json(client):
    """Malformed POST bodies must return the documented HTTP 422."""

    response = client.post(
        "/v1/assignments",
        content=b"\xff\xfe\xfa",
        headers={
            "Content-Type": "application/json"
        },
    )

    problem = assert_problem(
        response,
        422,
        "validation-failed",
    )

    assert any(
        error["field"] == "body"
        for error in problem["errors"]
    )


def test_update_assignment_rejects_malformed_json(client):
    """Malformed PATCH bodies must return the documented HTTP 422."""

    response = client.patch(
        "/v1/assignments/asg_unknown",
        content=b"\xff\xfe\xfa",
        headers={
            "Content-Type": "application/json"
        },
    )

    problem = assert_problem(
        response,
        422,
        "validation-failed",
    )

    assert any(
        error["field"] == "body"
        for error in problem["errors"]
    )
