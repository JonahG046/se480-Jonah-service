"""Main application for the Student Assignment Tracker API."""

from fastapi import FastAPI

from app import observability, store
from app.errors import install as install_errors
from app.routers import assignments, courses, students

# An environment setting can intentionally fail a deployment.
observability.fail_startup_if_asked()

app = FastAPI(
    title="Student Assignment Tracker API",
    version="1.0.0",
    description=(
        "An API that helps students track assignments and deadlines across multiple courses."
    ),
)

# Register exception handling and request observability.
install_errors(app)
observability.install(app)

# Preserve all seven versioned API operations.
app.include_router(students.router)
app.include_router(courses.router)
app.include_router(assignments.router)


@app.get("/", include_in_schema=False)
def hello():
    """Preserve the original Lab 1 greeting."""

    return {"message": "Hello to you as well. Tomorrow is the Halloween!"}


@app.get("/health", include_in_schema=False)
def health():
    """Return basic operational health and in-memory store counts."""

    return observability.health_report(
        {
            "students": len(store.STUDENTS),
            "courses": len(store.COURSES),
            "assignments": len(store.ASSIGNMENTS),
        }
    )


@app.get("/metrics", include_in_schema=False)
def metrics():
    """Return Prometheus-compatible metrics."""

    return observability.metrics_response()
