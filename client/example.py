
"""Example client for the Student Assignment Tracker API.

Run:
    python client/example.py

Or choose a local server:
    python client/example.py --base-url http://127.0.0.1:8000

The example uses HTTPX2 and a 60-second timeout to accommodate
cold starts on the deployed Render service.
"""

import argparse
from datetime import datetime, timedelta, timezone

import httpx2 as httpx


DEFAULT_BASE_URL = "https://se480-jonah-service.onrender.com"


def show_problem(response) -> None:
    """Display a ProblemDetails response in readable language."""

    try:
        problem = response.json()
    except ValueError:
        print("The server did not return a JSON error.")
        print(response.text)
        return

    print(f"Error: {problem.get('title', 'Unknown error')}")
    print(f"Details: {problem.get('detail', 'No details provided')}")

    for error in problem.get("errors", []):
        field = error.get("field", "unknown")
        message = error.get("message", "is invalid")
        print(f"  - {field}: {message}")


def run_example(base_url: str) -> None:
    api_url = base_url.rstrip("/")

    if not api_url.endswith("/v1"):
        api_url += "/v1"

    print(f"Connecting to {api_url}")
    print()

    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        # 1. Discover available students.
        students_response = client.get(f"{api_url}/students")
        students_response.raise_for_status()

        students = students_response.json()

        print("Available students:")
        for student in students:
            print(f"  {student['id']}: {student['name']}")

        print()

        # 2. Discover available courses.
        courses_response = client.get(f"{api_url}/courses")
        courses_response.raise_for_status()

        courses = courses_response.json()

        print("Available courses:")
        for course in courses:
            print(f"  {course['id']}: {course['code']}")

        print()

        if not students or not courses:
            print("No sample students or courses are available.")
            return

        # 3. Create a real assignment using discovered IDs.
        deadline = datetime.now(timezone.utc) + timedelta(days=7)

        assignment_data = {
            "student_id": students[0]["id"],
            "course_id": courses[0]["id"],
            "title": "Example Client Assignment",
            "due_at": deadline.isoformat(),
        }

        created_response = client.post(
            f"{api_url}/assignments",
            json=assignment_data,
        )

        if created_response.status_code != 201:
            print("Assignment creation failed.")
            show_problem(created_response)
            return

        created = created_response.json()

        print("Assignment created successfully!")
        print(f"  ID: {created['id']}")
        print(f"  Title: {created['title']}")
        print(f"  Status: {created['status']}")
        print(f"  Deadline: {created['due_at']}")
        print(f"  Location: {created_response.headers.get('Location')}")
        print()

        # 4. Intentionally send invalid data.
        # The contract requires a date-time string, not a number.
        invalid_data = {
            **assignment_data,
            "due_at": 0,
        }

        invalid_response = client.post(
            f"{api_url}/assignments",
            json=invalid_data,
        )

        print("Demonstrating a validation error:")
        print(f"HTTP status: {invalid_response.status_code}")

        if invalid_response.status_code != 422:
            raise RuntimeError(
                "Expected 422 for an invalid numeric deadline, "
                f"but received {invalid_response.status_code}."
            )

        show_problem(invalid_response)

        print()
        print("Example client finished successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Demonstrate the Student Assignment Tracker API."
    )

    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="Service URL without /v1 (or with /v1 already included).",
    )

    args = parser.parse_args()

    try:
        run_example(args.base_url)
    except httpx.HTTPError as error:
        print(f"Could not communicate with the API: {error}")
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
