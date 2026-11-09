
"""Assignment endpoints for the Student Assignment Tracker.

Implements the operations defined in openapi.yaml.
Assignments are stored in memory for Lab 3.
"""

from fastapi import APIRouter, Query, Response

from app import rules, store
from app.errors import (
    Conflict,
    NotFound,
    ProblemDetails,
)
from app.models import (
    Assignment,
    AssignmentCreate,
    AssignmentUpdate,
)


router = APIRouter(prefix="/v1", tags=["Assignments"])


# Reusable documentation for our ProblemDetails responses.
PROBLEM = {
    "model": ProblemDetails,
    "content": {"application/problem+json": {}},
}

VALIDATION = {
    422: {
        **PROBLEM,
        "description": "The request contains missing or invalid information.",
    }
}

NOT_FOUND = {
    404: {
        **PROBLEM,
        "description": "The requested resource was not found.",
    }
}

CONFLICT = {
    409: {
        **PROBLEM,
        "description": (
            "A completed assignment must be reopened before "
            "its deadline can be changed."
        ),
    }
}


def assignment_or_404(assignment_id: str) -> Assignment:
    """Return an assignment or raise a not-found error."""

    assignment = store.ASSIGNMENTS.get(assignment_id)

    if assignment is None:
        raise NotFound(
            f"No assignment exists with ID {assignment_id}. "
            "Check the ID and try again."
        )

    return assignment


def student_exists(student_id: str) -> None:
    """Verify that a student exists."""

    if student_id not in store.STUDENTS:
        raise NotFound(
            f"No student exists with ID {student_id}. "
            "Use GET /v1/students to see available students."
        )


def course_exists(course_id: str) -> None:
    """Verify that a course exists."""

    if course_id not in store.COURSES:
        raise NotFound(
            f"No course exists with ID {course_id}. "
            "Use GET /v1/courses to see available courses."
        )


@router.get(
    "/assignments",
    summary="List assignments",
    description=(
        "Returns assignments in the system. "
        "The optional student_id filter limits results to "
        "one student. An unknown student returns 404."
    ),
    response_model=list[Assignment],
    response_model_exclude_none=True,
    responses={**VALIDATION, **NOT_FOUND},
)
def list_assignments(
    student_id: str | None = Query(
        default=None,
        min_length=1,
        description="Optional student ID used to filter assignments.",
    ),
) -> list[Assignment]:
    """Return all assignments or those belonging to one student."""

    if student_id is not None:
        student_exists(student_id)

        return [
            assignment
            for assignment in store.ASSIGNMENTS.values()
            if assignment.student_id == student_id
        ]

    return list(store.ASSIGNMENTS.values())


@router.post(
    "/assignments",
    status_code=201,
    summary="Create an assignment",
    description=(
        "Creates an assignment for an existing student "
        "and course. New assignments start as pending. "
        "The service generates the assignment ID and "
        "updated_at timestamp."
    ),
    response_model=Assignment,
    response_model_exclude_none=True,
    responses={
        201: {
            "description": "Assignment created successfully.",
            "headers": {
                "Location": {
                    "description": "URL path of the new assignment.",
                    "schema": {"type": "string"},
                }
            },
        },
        **VALIDATION,
        **NOT_FOUND,
    },
)
def create_assignment(
    body: AssignmentCreate,
    response: Response,
) -> Assignment:
    """Create and store a new assignment."""

    student_exists(body.student_id)
    course_exists(body.course_id)

    assignment = Assignment(
        **body.model_dump(),
        id=store.new_assignment_id(),
        status="pending",
        updated_at=store.current_time(),
    )

    store.ASSIGNMENTS[assignment.id] = assignment

    response.headers["Location"] = (
        f"/v1/assignments/{assignment.id}"
    )

    return assignment


@router.get(
    "/assignments/{assignment_id}",
    summary="Get assignment details",
    description="Returns one assignment using its unique ID.",
    response_model=Assignment,
    response_model_exclude_none=True,
    responses={**NOT_FOUND},
)
def get_assignment(assignment_id: str) -> Assignment:
    """Retrieve one assignment."""

    return assignment_or_404(assignment_id)


@router.patch(
    "/assignments/{assignment_id}",
    summary="Update an assignment",
    description=(
        "Updates the title, course, deadline, or status "
        "of an existing assignment. "
        "The student_id cannot be changed. "
        "A completed assignment must first be reopened "
        "in a separate PATCH request that sets its status "
        "to pending before its due date can be changed. "
        "Otherwise, the service returns 409 Conflict. "
        "Simultaneous updates from different clients are "
        "a known risk. Concurrency protection is not "
        "included in this initial version."
    ),
    response_model=Assignment,
    response_model_exclude_none=True,
    responses={**VALIDATION, **NOT_FOUND, **CONFLICT},
)
def update_assignment(
    assignment_id: str,
    body: AssignmentUpdate,
) -> Assignment:
    """Update an assignment while enforcing its business rules."""

    assignment = assignment_or_404(assignment_id)

    changes = body.model_dump(exclude_unset=True)

    # This rule applies even when the same PATCH also
    # attempts to reopen the completed assignment.
    if rules.deadline_change_blocked(assignment, changes):
        raise Conflict(
            "Reopen the assignment before changing its deadline. "
            "First set its status to pending in a separate request."
        )

    # An assignment can change courses, but only to
    # another course that already exists.
    if "course_id" in changes:
        course_exists(changes["course_id"])

    updated = assignment.model_copy(
        update={
            **changes,
            "updated_at": store.current_time(),
        }
    )

    store.ASSIGNMENTS[assignment_id] = updated

    return updated


@router.delete(
    "/assignments/{assignment_id}",
    status_code=204,
    summary="Delete an assignment",
    description=(
        "Permanently deletes an existing assignment. "
        "Returns 204 on success with no response body. "
        "An unknown assignment ID returns 404."
    ),
    response_class=Response,
    responses={**NOT_FOUND},
)
def delete_assignment(assignment_id: str) -> Response:
    """Permanently remove an existing assignment."""

    assignment_or_404(assignment_id)

    del store.ASSIGNMENTS[assignment_id]

    return Response(status_code=204)
