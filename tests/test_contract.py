
"""Contract and API drift tests for the Student Assignment Tracker."""

from urllib.parse import urlsplit

import schemathesis
import yaml
from fastapi.testclient import TestClient
from hypothesis import settings

from app import store
from app.main import app


# Load the API contract written in Lab 2.
schema = schemathesis.openapi.from_path("openapi.yaml")

# Send generated requests directly to FastAPI, not to Render.
schema.app = app
schema.config.update(base_url="http://testserver/v1")


@schema.parametrize()
@settings(max_examples=25, deadline=None)
def test_contract(case):
    """Check generated requests and responses against openapi.yaml."""

    # Each generated case gets a clean in-memory assignment store.
    store.reset()

    case.call_and_validate()


def test_api_drift():
    """Check that the implemented operations match the design."""

    with open("openapi.yaml", encoding="utf-8") as file:
        specification = yaml.safe_load(file)

    # Resolve the version variable in the server URL.
    server = specification["servers"][0]
    server_url = server["url"]

    for name, settings in server.get("variables", {}).items():
        server_url = server_url.replace(
            "{" + name + "}",
            settings["default"],
        )

    base_path = urlsplit(server_url).path.rstrip("/")

    http_methods = {
        "get", "post", "put", "patch",
        "delete", "head", "options", "trace",
    }

    # Operations declared in our hand-written API specification.
    expected = {
        (base_path + path, method.upper())
        for path, path_item in specification["paths"].items()
        for method in path_item
        if method.lower() in http_methods
    }

    # Operations generated from the actual FastAPI application.
    response = TestClient(app).get("/openapi.json")
    assert response.status_code == 200

    generated = response.json()

    actual = {
        (path, method.upper())
        for path, path_item in generated["paths"].items()
        for method in path_item
        if method.lower() in http_methods
    }

    assert actual == expected, (
        f"Missing from code: {expected - actual}\n"
        f"Missing from spec: {actual - expected}"
    )
