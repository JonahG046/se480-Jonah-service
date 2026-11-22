
# Postmortem — Lost Assignment Update

**Date:** November 22, 2026  
**Service:** Student Assignment Tracker API  
**Severity:** Test-only incident; no real users affected  
**Status:** Reproduced; known limitation remains open

## Summary

Two clients updated the same assignment at nearly the same time.
Both PATCH requests returned HTTP 200, but one change was lost.

For students, this could mean that an assignment appears to save
correctly while information they entered is silently overwritten.

The failure was reproduced locally using
`tests/test_concurrency.py`. This was not a production incident.

## Impact

One test assignment was affected during the reproduction.

Both PATCH requests succeeded, but only the course change remained.
The title reverted to its original value.

No real student data was involved. The observed failure occurred
during a short local test on November 22, 2026.

## Detection

The test compared the final assignment against both requested
changes and found that one was missing.

The request logs showed two successful responses. Neither was
reported as an HTTP error.

This is an observability gap: successful HTTP responses do not
prove that simultaneous changes were preserved.

## Timeline

All times are UTC on November 22, 2026.

- 18:04:02.503 — A test assignment was created (HTTP 201).
- 18:04:02.517 — One PATCH completed (HTTP 200).
- 18:04:02.518 — The other PATCH completed (HTTP 200).
- The test inspected the assignment after both updates.
- The course was changed to `crs_c9n32`.
- The title remained `Original Assignment`.
- Pytest recorded the known failure as XFAIL.

## Contributing Factors

- Assignments are stored in an in-memory dictionary.
- Updates read an assignment, modify a copy, and replace the
  stored record.
- No version check detects whether another request changed
  the record after it was read.
- Both requests can independently succeed while one overwrites
  the other's changes.
- HTTP success metrics alone cannot detect the lost update.

## What Went Well

The failure was reproducible with a controlled test.

Request IDs and structured logs made it possible to identify
the individual HTTP requests and their responses.

The test documents the limitation without making CI fail
because of a known, intentionally deferred issue.

## What the Service Would Have Shown

**Request logs:** Two successful PATCH responses, both with request
IDs, route templates, and durations. The logs do not reveal that
one field change was lost.

**Health:** The current health design reports process uptime and
record counts, not whether concurrent changes were preserved.
The health response was not separately captured during this test.

**Metrics:** The two successful PATCH requests contribute to
the 2xx request count. The deadline-conflict counter does not
detect this failure because no completed-assignment deadline
rule was violated.

**Notifications:** No failure-notification result was collected
from this local reproduction. That will be evaluated separately
during the Render deployment experiment.

## Action Items

| Action | Owner | Target date | Home |
|---|---|---|---|
| Evaluate version checks or optimistic concurrency control | Project maintainer | Dec. 4, 2026 | Final |
| Add a regression test requiring both updates to be preserved or one to return a conflict | Project maintainer | Dec. 4, 2026 | Final |
| Document the concurrency limitation and link the reproduction | Project maintainer | Nov. 22, 2026 | Milestone 2 |
| Keep the current XFAIL test until concurrency protection is implemented | Project maintainer | Dec. 4, 2026 | Final |

## Current Resolution

The issue remains open intentionally.

The completed-assignment deadline rule is a separate protection:
it returns HTTP 409 when someone tries to change a completed
assignment's due date.

The concurrency failure demonstrates that unrelated simultaneous
updates may still overwrite one another.

**Reproduction:** `tests/test_concurrency.py`
