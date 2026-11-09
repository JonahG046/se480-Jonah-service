
"""Business rules for the Student Assignment Tracker.

These functions contain application rules without depending
on FastAPI, HTTP requests, or database storage.

Keeping rules separate makes them easier to test.
"""

from typing import Any

from app.models import Assignment


def deadline_change_blocked(
    assignment: Assignment,
    changes: dict[str, Any],
) -> bool:
    """Check whether an update violates the completed-assignment rule.

    A completed assignment cannot have its due date changed.

    Reopening and changing the deadline in the same request
    is not allowed. The student must first send a separate
    update setting status to pending.
    """

    if assignment.status != "completed":
        return False

    if "due_at" not in changes:
        return False

    new_deadline = changes["due_at"]

    return new_deadline != assignment.due_at
