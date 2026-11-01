# SE 480 - Student Assignment Tracker API

**Deployed Application:** https://se480-jonah-service.onrender.com

**Health Check:** https://se480-jonah-service.onrender.com/health

This project is a Student Assignment Tracker API for SE 480. The goal is to help students manage assignments and deadlines across multiple courses.

Lab 1 focused on setting up the FastAPI service, deploying it to Render, and configuring GitHub Actions. Lab 2 focuses on designing the assignment tracking API using OpenAPI and testing it with a mock server before implementing the endpoints.

## How to Run It

1. Open this repository in GitHub Codespaces.
2. Wait for the development container to finish building.
3. Open a terminal and run:

   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```

4. Open the forwarded port 8000 in your browser.
5. Visit `/` to see the greeting and `/health` to check the service status.

Keep port 8000 private in Codespaces.

To run the automated FastAPI tests:

```bash
python -m pytest -q
```

GitHub Actions automatically runs the smoke tests when changes are pushed to the repository. The deployed smoke test also checks the public Render service's health endpoint.

## Mock It

Lab 2 introduces the Student Assignment Tracker API specification in `openapi.yaml`. The specification defines the resources, endpoints, expected responses, and error handling before the endpoints are implemented.

The API has three main resources: students, courses, and assignments. Students and courses are read-only, while assignments can be created, viewed, updated, and deleted.

### Validate the API Specification

Run the following command in the Codespaces terminal:

```bash
make lint
```

This uses Spectral to validate `openapi.yaml` and check for errors or warnings.

### Start the Mock Server

Run:

```bash
make mock
```

This starts the Prism mock server on port 4010.

Open a second terminal and run:

```bash
curl -i http://127.0.0.1:4010/assignments
```

The mock server should return a `200 OK` response containing an example assignment.

To test a `404 Not Found` response:

```bash
curl -i -H 'Prefer: code=404' http://127.0.0.1:4010/assignments/asg_unknown
```

This returns an example error using the `ProblemDetails` format defined in our API specification.

Prism does not store or modify actual assignment data. It generates responses based on the OpenAPI specification so the API can be tested before implementation.

The mock endpoints do not include `/v1` in their request paths. The version prefix is defined in the API's deployed base URL.

Stop the mock server with `Ctrl + C` when finished.

## What's in the Repo

- `app/main.py` — FastAPI application and existing service routes.
- `tests/` — Automated tests for the FastAPI service.
- `.devcontainer/` — GitHub Codespaces configuration, including Python and Node.js.
- `.github/workflows/ci.yml` — GitHub Actions workflow for automated smoke tests.
- `requirements.txt` — Python dependencies.
- `Dockerfile` — Configuration used to deploy the service to Render.
- `openapi.yaml` — OpenAPI 3.1 specification for the Student Assignment Tracker.
- `.spectral.yaml` — Spectral configuration used to validate the API specification.
- `Makefile` — Commands for running Spectral and starting the Prism mock server.
- `README.md` — Project setup, testing, and documentation.

## Help Received

I followed the course handouts, lecture slides, and provided repository template to complete the labs. I also used ChatGPT to help understand some of the instructions, work through the API design decisions, and troubleshoot issues during setup and testing.

## AI Tools Used

I used ChatGPT as a step-by-step guide throughout Labs 1 and 2.

For Lab 1, I used it to better understand the setup instructions, troubleshoot GitHub and Render configuration, and help write the README. The FastAPI application and CI workflow came from the course template.

For Lab 2, I used ChatGPT to help develop the Student Assignment Tracker design sheet and draft sections of `openapi.yaml`, including the resource schemas, reusable error responses, and API endpoints. I also used it to troubleshoot the Node.js setup and help document the Spectral and Prism commands.

I reviewed the API design and ran the Spectral validation and Prism mock tests in Codespaces to verify the specification.