
"""Shared error handling for the Student Assignment Tracker API.

All API errors follow the ProblemDetails format defined in
openapi.yaml and use application/problem+json.
"""

import re

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException


PROBLEM_BASE = "https://se480-jonah-service.onrender.com/problems/"
PROBLEM_MEDIA_TYPE = "application/problem+json"


class FieldError(BaseModel):
    """Identifies a field that failed validation."""

    field: str = Field(
        description="Name of the invalid field."
    )

    message: str = Field(
        description="Explanation of what needs correcting."
    )


class ProblemDetails(BaseModel):
    """The error response defined by our OpenAPI specification."""

    type: str = Field(
        description="Stable identifier for the kind of error."
    )

    title: str = Field(
        description="Short explanation of the error."
    )

    status: int = Field(
        description="HTTP status code."
    )

    detail: str = Field(
        description="Explanation of what went wrong and how to fix it."
    )

    instance: str = Field(
        description="API request path where the error occurred."
    )

    errors: list[FieldError] | None = Field(
        default=None,
        description="Specific fields that failed validation."
    )


class Problem(Exception):
    """Base exception for errors the application expects."""

    slug = "about:blank"
    status = 500
    title = "Something went wrong"

    def __init__(self, detail: str, **extra):
        super().__init__(detail)
        self.detail = detail
        self.extra = extra


class ValidationFailed(Problem):
    """Request data is missing or invalid."""

    slug = "validation-failed"
    status = 422
    title = "Invalid assignment information"


class NotFound(Problem):
    """A requested resource does not exist."""

    slug = "not-found"
    status = 404
    title = "Resource not found"


class Conflict(Problem):
    """An assignment cannot be changed in its current state."""

    slug = "completed-assignment"
    status = 409
    title = "Completed assignment cannot be rescheduled"


def problem_response(
    request: Request,
    status: int,
    slug: str,
    title: str,
    detail: str,
    **extra,
) -> JSONResponse:
    """Build an RFC 9457 ProblemDetails response."""

    type_url = (
        slug
        if slug.startswith("about:")
        else PROBLEM_BASE + slug
    )

    body = ProblemDetails(
        type=type_url,
        title=title,
        status=status,
        detail=detail,
        instance=request.url.path,
        **extra,
    )

    return JSONResponse(
        content=body.model_dump(exclude_none=True),
        status_code=status,
        media_type=PROBLEM_MEDIA_TYPE,
    )


# Human-readable validation messages.
_MESSAGES = {
    "missing": "is required",
    "timezone_aware": (
        "needs a time zone offset, for example "
        "2026-11-15T23:59:00-06:00"
    ),
}


def _allowed_methods(request: Request) -> str:
    """Find every supported HTTP method for the requested path.

    Check FastAPI's registered routes first. If route matching does
    not identify the methods, use the generated OpenAPI document.

    This ensures a 405 response includes the required Allow header
    with all methods supported at the requested path.
    """

    path = request.scope.get("path", "")
    methods: set[str] = set()

    # First, examine registered FastAPI routes.
    for route in request.app.router.routes:
        path_regex = getattr(route, "path_regex", None)

        if path_regex is not None and path_regex.fullmatch(path):
            methods.update(
                getattr(route, "methods", None) or set()
            )

    # Fallback: use the generated OpenAPI operations.
    if not methods:
        spec = request.app.openapi()

        for template, operations in spec.get("paths", {}).items():
            segments = template.split("/")

            pattern = "/".join(
                r"[^/]+"
                if segment.startswith("{") and segment.endswith("}")
                else re.escape(segment)
                for segment in segments
            )

            if re.fullmatch(pattern, path):
                for method in operations:
                    if method.lower() in {
                        "get",
                        "post",
                        "put",
                        "patch",
                        "delete",
                        "head",
                        "options",
                        "trace",
                    }:
                        methods.add(method.upper())

    return ", ".join(sorted(methods))


def install(app: FastAPI) -> None:
    """Register shared exception handlers with the application."""

    @app.exception_handler(Problem)
    async def handle_problem(
        request: Request,
        exc: Problem,
    ):
        """Convert expected application errors to ProblemDetails."""

        return problem_response(
            request,
            exc.status,
            exc.slug,
            exc.title,
            exc.detail,
            **exc.extra,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation(
        request: Request,
        exc: RequestValidationError,
    ):
        """Convert Pydantic validation errors into HTTP 422 problems."""

        errors = []

        for err in exc.errors():
            location = [
                str(part)
                for part in err.get("loc", [])
                if part not in ("body", "query", "path")
            ]

            errors.append(
                {
                    "field": ".".join(location) or "body",
                    "message": _MESSAGES.get(
                        err.get("type"),
                        err.get("msg", "is invalid"),
                    ),
                }
            )

        return problem_response(
            request=request,
            status=422,
            slug="validation-failed",
            title=ValidationFailed.title,
            detail="Check the invalid fields and try again.",
            errors=errors,
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http(
        request: Request,
        exc: StarletteHTTPException,
    ):
        """Handle framework errors using our ProblemDetails format.

        This includes unknown paths, unsupported HTTP methods,
        and malformed request bodies that FastAPI cannot parse.
        """

        # FastAPI can raise HTTP 400 before running a router
        # when the body cannot be decoded or parsed.
        #
        # Our OpenAPI contract documents HTTP 422 for invalid
        # request bodies, so convert this specific error.
        #
        # Schemathesis discovered this discrepancy when it
        # generated malformed JSON for POST and PATCH.
        if (
            exc.status_code == 400
            and str(exc.detail) == "There was an error parsing the body"
        ):
            return problem_response(
                request=request,
                status=422,
                slug="validation-failed",
                title=ValidationFailed.title,
                detail=(
                    "The request body could not be parsed. "
                    "Send a valid JSON document."
                ),
                errors=[
                    {
                        "field": "body",
                        "message": (
                            "The request body is malformed "
                            "or incorrectly encoded."
                        ),
                    }
                ],
            )

        # Unknown API path.
        if exc.status_code == 404:
            response = problem_response(
                request,
                404,
                "not-found",
                "Resource not found",
                (
                    "There is nothing at this path. "
                    "See /docs for the available operations."
                ),
            )

        # Unsupported HTTP method.
        elif exc.status_code == 405:
            response = problem_response(
                request,
                405,
                "about:blank",
                "Method not allowed",
                (
                    "This path does not support the "
                    "requested HTTP method."
                ),
            )

        # Other framework-generated HTTP errors.
        else:
            response = problem_response(
                request,
                exc.status_code,
                "about:blank",
                "Request could not be completed",
                str(exc.detail),
            )

        # Preserve headers supplied by Starlette.
        response.headers.update(exc.headers or {})

        # RFC 9110 requires an Allow header on 405 responses.
        # Include all supported methods for the requested path.
        if exc.status_code == 405:
            response.headers["Allow"] = _allowed_methods(request)

        return response
