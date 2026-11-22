
# Service Level Objective — Student Assignment Tracker

## The Promise

At least 95% of requests to the assignment collection
will complete within 500 milliseconds.

## User Journey

This SLO protects students who list or create assignments
through `/v1/assignments`.

Students should be able to check deadlines and submit
assignment information without unnecessary delays.

## Service Level Indicator (SLI)

The SLI measures the percentage of requests to
`/v1/assignments` completed within 500 milliseconds.

SLI = Good requests / Valid requests × 100

- Good requests: Requests completed in 0.5 seconds or less.
- Valid requests: All completed requests matching
  `/v1/assignments`, including responses with error statuses.

We include errors because this SLO measures response time,
not whether a request was successful.

The metric comes from the Prometheus duration histogram:

- Good: `http_request_duration_seconds_bucket`
  with `route="/v1/assignments"` and `le="0.5"`
- Total: `http_request_duration_seconds_count`
  with `route="/v1/assignments"`

## Target and Measurement Window

- Target: 95%
- Maximum duration: 500 milliseconds
- Window: Since the application process started
- Source: `/metrics`
- Process start time: `/health` (`started_at`)

Metrics reset whenever the service restarts. This is
not a rolling seven-day measurement.

## Exclusions

- `/health` and `/metrics` are excluded because they
  are operational requests, not student interactions.
- Other API routes are outside this particular SLO.
- Cold-start delays before the application starts
  cannot be measured by the in-process histogram.

The SLO does not currently measure client network
latency or the time spent waiting for a sleeping
Render instance to start.

## Measurement

The SLO will be measured against the deployed Render
service using a batch of requests.

Record the actual results here after deployment:

- Measurement date: Pending
- Process started_at: Pending
- Good requests: Pending
- Total requests: Pending
- Calculated SLI: Pending

Calculation:

SLI = (Good / Total) × 100

The local JSON request logs will also be checked
against the same latency threshold to determine
whether the observed counts agree.

## Error Budget

The error budget is 5% of eligible requests exceeding
500 milliseconds.

If the budget is exhausted, improving performance
and investigating slow requests will take priority
over adding new features until the service returns
to its target.

## Known Limitations

The histogram measures request processing within
the application process.

It cannot show whether simultaneous updates
overwrote an assignment. That separate reliability
issue is documented in `docs/postmortem.md`.
