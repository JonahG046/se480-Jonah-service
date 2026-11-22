
# Milestone 2 — Student Assignment Tracker

**Date:** November 22, 2026

**GitHub Repository:** https://github.com/JonahG046/se480-Jonah-service

**Deployed API:** https://se480-jonah-service.onrender.com

**API Documentation:** https://se480-jonah-service.onrender.com/docs

**Demo Video:** Will be submitted separately in D2L.

## What Shipped

The Student Assignment Tracker is deployed on Render and supports all seven API operations from my original proposal.

Students and courses are read-only. Assignments can be created, listed, filtered by student, viewed individually, updated, and deleted.

The API also enforces the completed-assignment deadline rule. If someone tries to change a completed assignment's deadline, the service returns HTTP 409 until the assignment is reopened.

I added ProblemDetails error handling, request IDs, structured JSON logging, health monitoring, and Prometheus metrics.

The latest local verification had 52 passing tests, one expected failure, and 99.37% coverage. The deployed service also completed 250 test requests with 100% finishing within 500 milliseconds.

## What Didn't Ship

The API still uses in-memory storage, so assignments disappear when the service restarts. Authentication and a user interface are also outside the current scope.

I reproduced a concurrency issue where two simultaneous updates return HTTP 200, but one change is lost. The test is documented as an expected failure rather than being silently ignored.

## Failure and Recovery

I intentionally caused a failed Render deployment using an environment variable. Render detected the failure, recorded it in the logs, and sent an email notification.

After removing the variable, the service deployed successfully again.

The concurrency issue and its impact are documented in `docs/postmortem.md`. The service-level objective and real measurements are documented in `docs/slo.md`.

## What's Next

For the final submission on December 4, 2026, I plan to review the concurrency problem, consider adding version checks to prevent lost updates, and complete the final testing and documentation.

Persistent storage and authentication remain possible future improvements, but they are not part of this milestone.
