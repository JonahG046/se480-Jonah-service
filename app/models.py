
"""Pydantic models for the Student Assignment Tracker API.

These models follow the schemas defined in openapi.yaml.

Input models contain fields supplied by clients, while the
full Assignment model includes server-generated fields.
"""

from datetime import datetime
from typing import Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


class Student(BaseModel):
    """A student who can have assignments."""

    id: str = Field(
        description="Unique identifier for the student.",
        examples=["stu_a7k92"],
    )

    name: str = Field(
        description="Student's name, supporting Unicode characters.",
        examples=["Alex Johnson"],
    )

    email: EmailStr = Field(
        description="Student's email address.",
        examples=["alex@example.edu"],
    )


class Course(BaseModel):
    """A course that assignments belong to."""

    id: str = Field(
        description="Unique identifier for the course.",
        examples=["crs_b8m21"],
    )

    code: str = Field(
        description="Course code used by the school.",
        examples=["SE480"],
    )

    name: str = Field(
        description="Full name of the course.",
        examples=["Software Engineering Project"],
    )


class AssignmentCreate(BaseModel):
    """Information required to create an assignment."""

    model_config = ConfigDict(extra="forbid")

    student_id: str = Field(
        description="Student who will own the assignment.",
        examples=["stu_a7k92"],
    )

    course_id: str = Field(
        description="Course the assignment belongs to.",
        examples=["crs_b8m21"],
    )

    title: str = Field(
        min_length=1,
        max_length=200,
        description="Name of the assignment.",
        examples=["Database Design Project"],
    )

    due_at: AwareDatetime = Field(
        description="Deadline with an explicit timezone offset.",
        examples=["2026-11-15T23:59:00-06:00"],
    )

    @field_validator("due_at", mode="before")
    @classmethod
    def validate_deadline_input(cls, value):
        """Reject numeric timestamps from incoming requests.

        OpenAPI requires due_at to be a date-time string.
        Pydantic normally accepts numeric Unix timestamps,
        which violates that contract.

        Datetime objects are allowed internally because the
        router passes an already-parsed datetime when building
        a complete Assignment model.
        """

        if not isinstance(value, (str, datetime)):
            raise ValueError(
                "due_at must be a date-time string "
                "with an explicit timezone offset"
            )

        return value


class Assignment(AssignmentCreate):
    """A complete assignment returned by the API."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(
        description="Unique identifier generated for the assignment.",
        examples=["asg_k9p32"],
        json_schema_extra={"readOnly": True},
    )

    status: Literal["pending", "completed"] = Field(
        description="Whether the assignment is finished.",
    )

    updated_at: AwareDatetime = Field(
        description="When the assignment was last updated.",
        examples=["2026-11-01T14:30:00-06:00"],
        json_schema_extra={"readOnly": True},
    )


class AssignmentUpdate(BaseModel):
    """Fields allowed when updating an existing assignment."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Updated assignment title.",
    )

    course_id: str | None = Field(
        default=None,
        description="Updated course identifier.",
    )

    due_at: AwareDatetime | None = Field(
        default=None,
        description=(
            "Updated deadline with an explicit timezone offset. "
            "A completed assignment must be reopened in a separate "
            "request before its deadline can change."
        ),
    )

    status: Literal["pending", "completed"] | None = Field(
        default=None,
        description="Updated completion status.",
    )

    @field_validator("due_at", mode="before")
    @classmethod
    def validate_deadline_input(cls, value):
        """Reject numeric timestamps during assignment updates."""

        if value is None:
            return value

        if not isinstance(value, (str, datetime)):
            raise ValueError(
                "due_at must be a date-time string "
                "with an explicit timezone offset"
            )

        return value

    @model_validator(mode="after")
    def validate_update(self):
        """Require at least one field and reject explicit null values."""

        changes = self.model_dump(exclude_unset=True)

        if not changes:
            raise ValueError(
                "At least one field must be provided."
            )

        if any(value is None for value in changes.values()):
            raise ValueError(
                "Updated fields cannot be null."
            )

        return self
