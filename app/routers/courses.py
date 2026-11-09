
"""Read-only course endpoints."""

from fastapi import APIRouter

from app import store
from app.models import Course


router = APIRouter(prefix="/v1", tags=["Courses"])


@router.get(
    "/courses",
    summary="List courses",
    description=(
        "Returns the courses available in the system. "
        "Course records are read-only in v1."
    ),
    response_model=list[Course],
    response_model_exclude_none=True,
)
def list_courses() -> list[Course]:
    """Return all available sample courses."""

    return list(store.COURSES.values())
