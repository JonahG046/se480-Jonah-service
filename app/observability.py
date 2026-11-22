"""Lab 5 observability for the Student Assignment Tracker.

Adds request IDs, JSON request logs, Prometheus metrics,
and basic service health information.
"""

import json
import os
import re
import secrets
import sys
import time
from datetime import UTC, datetime

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

REQUEST_ID_HEADER = "X-Request-ID"
UNMATCHED = "unmatched"

# Render polls /health frequently. Operational requests are
# excluded from user traffic logs and SLO measurements.
QUIET_PATHS = frozenset({"/health", "/metrics"})

# Accepted caller IDs cannot contain newlines or injected JSON.
ACCEPTABLE_ID = re.compile(r"[A-Za-z0-9._-]{8,64}")

STARTED_AT = datetime.now(UTC)

REQUESTS = Counter(
    "http_requests_total",
    "Requests by route template and status class.",
    ["route", "status"],
)

DURATION = Histogram(
    "http_request_duration_seconds",
    "Request duration in seconds by route template.",
    ["route"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

# Specific to our completed-assignment business rule.
DEADLINE_CONFLICTS = Counter(
    "assignment_deadline_conflicts_total",
    "Rejected attempts to change completed assignment deadlines.",
)


def fail_startup_if_asked() -> None:
    """Support a reversible failed deployment for Lab 5."""

    if os.environ.get("LAB5_FAIL_STARTUP") == "1":
        raise SystemExit("LAB5_FAIL_STARTUP=1: intentional startup failure.")


def request_id(request: Request) -> str:
    """Return the current request ID."""

    return getattr(request.state, "request_id", "-")


def route_template(request: Request) -> str:
    """Return the route template without exposing resource IDs."""

    route = request.scope.get("route")
    return getattr(route, "path", None) or UNMATCHED


def log_line(**fields) -> None:
    """Write one structured JSON record to standard output."""

    timestamp = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")

    record = {
        "ts": timestamp,
        **fields,
    }

    sys.stdout.write(json.dumps(record, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def record_request(
    request: Request,
    status: int,
    started: float,
) -> None:
    """Record request duration, status and a single log line."""

    elapsed = time.perf_counter() - started
    route = route_template(request)

    status_class = f"{status // 100}xx"

    REQUESTS.labels(
        route=route,
        status=status_class,
    ).inc()

    DURATION.labels(route=route).observe(elapsed)

    log_line(
        level="ERROR" if status >= 500 else "INFO",
        request_id=request_id(request),
        method=request.method,
        route=route,
        status=status,
        duration_ms=round(elapsed * 1000),
    )


async def observe(request: Request, call_next) -> Response:
    """Give every request an ID and measure user requests."""

    incoming = request.headers.get(REQUEST_ID_HEADER, "")

    request.state.request_id = (
        incoming if ACCEPTABLE_ID.fullmatch(incoming) else secrets.token_hex(8)
    )

    quiet = request.url.path in QUIET_PATHS
    started = time.perf_counter()

    try:
        response = await call_next(request)

    except Exception:
        # Unexpected errors are handled outside this middleware.
        # Record the request here before re-raising.
        if not quiet:
            record_request(request, 500, started)

        raise

    response.headers[REQUEST_ID_HEADER] = request_id(request)

    if not quiet:
        record_request(request, response.status_code, started)

    return response


def health_report(store_counts: dict[str, int]) -> dict:
    """Return service status, uptime, revision and record counts."""

    uptime = datetime.now(UTC) - STARTED_AT

    return {
        "status": "ok",
        "started_at": STARTED_AT.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "uptime_seconds": int(uptime.total_seconds()),
        "commit": (os.environ.get("RENDER_GIT_COMMIT", "")[:7] or "unknown"),
        "store": store_counts,
    }


def metrics_response() -> Response:
    """Expose metrics using the Prometheus text format."""

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


def install(app: FastAPI) -> None:
    """Register the monitoring middleware."""

    app.middleware("http")(observe)
