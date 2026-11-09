
"""Read-only student endpoints."""

from fastapi import APIRouter

from app import store
from app.models import Student


router = APIRouter(prefix="/v1", tags=["Students"])


@router.get(
    "/students",
    summary="List students",
    description=(
        "Returns the students available in the system. "
        "Student records are read-only in v1."
    ),
    response_model=list[Student],
    response_model_exclude_none=True,
)
def list_students() -> list[Student]:
    """Return all available sample students."""

    return list(store.STUDENTS.values())
