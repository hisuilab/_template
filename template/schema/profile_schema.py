"""Validation and immutable representation of profile.toml."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from template.schema._toml import require_str, require_table
from template.schema.errors import SchemaError


CATEGORIES = ("cli", "web", "library")


@dataclass(frozen=True)
class ProfileSchema:
    """Validated, immutable representation of a profile.toml document."""

    name: str
    summary: str
    category: str
    parts: tuple[str, ...]
    variables: Mapping[str, str]


def validate_profile(data: dict, *, source: str) -> ProfileSchema:
    """Validate a parsed profile.toml table and return its immutable representation.

    Raises:
        SchemaError: If a required field is missing, parts is empty or not
            a list of strings, or variables has a non-string value.
    """
    profile = require_table(data, "profile", source=source)

    name = require_str(profile, "name", source=source, table_name="profile")
    summary = require_str(profile, "summary", source=source, table_name="profile")
    category = require_str(profile, "category", source=source, table_name="profile")
    if category not in CATEGORIES:
        raise SchemaError(
            f"category must be one of {CATEGORIES}, got {category!r}",
            source=source,
            field="profile.category",
        )

    raw_parts = profile.get("parts")
    if (
        not isinstance(raw_parts, list)
        or not raw_parts
        or not all(isinstance(item, str) for item in raw_parts)
    ):
        raise SchemaError(
            "parts must be a non-empty list of strings", source=source, field="profile.parts"
        )
    parts = tuple(raw_parts)

    raw_variables = data.get("variables", {})
    if not isinstance(raw_variables, dict) or not all(
        isinstance(value, str) for value in raw_variables.values()
    ):
        raise SchemaError(
            "variables must be a table of string values", source=source, field="variables"
        )
    variables = MappingProxyType(dict(raw_variables))

    return ProfileSchema(
        name=name, summary=summary, category=category, parts=parts, variables=variables
    )
