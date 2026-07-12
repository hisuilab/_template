"""Internal helpers shared by part_schema.py and profile_schema.py."""

from __future__ import annotations

from template.schema.errors import SchemaError


def require_table(data: dict, key: str, *, source: str) -> dict:
    """Return data[key] if it is a table, else raise SchemaError."""
    value = data.get(key)
    if not isinstance(value, dict):
        raise SchemaError(f"[{key}] table is required", source=source, field=key)
    return value


def require_str(table: dict, key: str, *, source: str, table_name: str) -> str:
    """Return table[key] if it is a non-empty string, else raise SchemaError."""
    value = table.get(key)
    if not isinstance(value, str) or not value:
        raise SchemaError(
            f"{key} is required and must be a non-empty string",
            source=source,
            field=f"{table_name}.{key}",
        )
    return value


def optional_str_list(
    table: dict, key: str, *, source: str, field_prefix: str = ""
) -> tuple[str, ...]:
    """Return table[key] (default []) as a tuple, requiring a list of strings."""
    value = table.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise SchemaError(
            f"{key} must be a list of strings", source=source, field=f"{field_prefix}{key}"
        )
    return tuple(value)
