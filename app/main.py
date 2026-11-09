
"""Main application for the Student Assignment Tracker API."""

from fastapi import FastAPI

from app.errors import install
from app.routers import assignments, courses, students


app = FastAPI(
    title="Student Assignment Tracker API",
    version="1.0.0",
    description=(
        "An API that helps students track assignments "
        "and deadlines across multiple courses."
    ),
)


# Register our shared ProblemDetails error handlers.
install(app)


# Register the seven API operations under /v1.
app.include_router(students.router)
app.include_router(courses.router)
app.include_router(assignments.router)


# Preserve the Lab 1 greeting.
# Operational endpoints are excluded from the API contract.
@app.get("/", include_in_schema=False)
def hello():
    return {
        "message": "Hello to you as well. Tomorrow is the Halloween!"
    }


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}
