
"""In-memory storage for the Student Assignment Tracker.

Students and courses contain sample records and are read-only in v1.
Assignments are created, updated, and deleted through the API.

Data is lost when the application restarts. Persistent storage is
outside the scope of Lab 3.
"""

import secrets
from datetime import datetime, timezone

from app.models import Assignment, Course, Student


# Sample students available to the API.
STUDENTS: dict[str, Student] = {
    "stu_a7k92": Student(
        id="stu_a7k92",
        name="Alex Johnson",
        email="alex@example.edu",
    ),
    "stu_b8m21": Student(
        id="stu_b8m21",
        name="Jordan Lee",
        email="jordan@example.edu",
    ),
}


# Sample courses available to the API.
COURSES: dict[str, Course] = {
    "crs_b8m21": Course(
        id="crs_b8m21",
        code="SE480",
        name="Software Engineering Project",
    ),
    "crs_c9n32": Course(
        id="crs_c9n32",
        code="CS340",
        name="Database Systems",
    ),
}


# Assignments start empty and are managed through the API.
ASSIGNMENTS: dict[str, Assignment] = {}


def new_assignment_id() -> str:
    """Generate a random, non-sequential assignment identifier."""

    while True:
        assignment_id = f"asg_{secrets.token_urlsafe(9)}"

        if assignment_id not in ASSIGNMENTS:
            return assignment_id


def current_time() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""

    return datetime.now(timezone.utc)


def reset() -> None:
    """Clear assignments between tests.

    Students and courses remain available because they are
    read-only sample data.
    """

    ASSIGNMENTS.clear()
