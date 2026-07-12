"""Errors raised while validating part.toml/profile.toml structures."""

from __future__ import annotations


class SchemaError(ValueError):
    """Raised when a parsed TOML table does not match the schema.

    Attributes:
        source: A human-readable identifier for the TOML being validated.
        field: The dotted field path that failed validation, if known.
    """

    def __init__(self, message: str, *, source: str, field: str | None = None) -> None:
        self.source = source
        self.field = field
        located = f"{source}: {field}: {message}" if field else f"{source}: {message}"
        super().__init__(located)
