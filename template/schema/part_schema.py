"""Validation and immutable representation of part.toml."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field

from template.schema._toml import optional_str_list, require_str, require_table
from template.schema.errors import SchemaError

_VALID_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*(/[a-zA-Z0-9][a-zA-Z0-9_-]*)*$")

LAYERS = ("base", "scale", "architecture", "starter", "style", "lang", "languages", "features")
STRATEGIES = ("error", "replace", "add", "append")
DEFAULT_STRATEGY = "error"


@dataclass(frozen=True)
class FileRule:
    """One [[files]] entry: a non-default placement strategy for a payload path."""

    path: str
    strategy: str = DEFAULT_STRATEGY


@dataclass(frozen=True)
class PartSchema:
    """Validated, immutable representation of a part.toml document."""

    id: str
    layer: str
    summary: str
    requires: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    placeholders_required: tuple[str, ...] = ()
    files: tuple[FileRule, ...] = ()
    variables: Mapping[str, str] = field(default_factory=dict)


def validate_part(data: dict, *, source: str) -> PartSchema:
    """Validate a parsed part.toml table and return its immutable representation.

    Raises:
        SchemaError: If a required field is missing, has the wrong type, or
            an enumerated field (layer/strategy) is out of range.
    """
    part = require_table(data, "part", source=source)

    layer = require_str(part, "layer", source=source, table_name="part")
    if layer not in LAYERS:
        raise SchemaError(
            f"layer must be one of {LAYERS}, got {layer!r}", source=source, field="part.layer"
        )

    part_id = require_str(part, "id", source=source, table_name="part")
    if not _VALID_ID_RE.match(part_id):
        raise SchemaError(
            f"part.id must match {_VALID_ID_RE.pattern!r}, got {part_id!r}",
            source=source,
            field="part.id",
        )
    summary = require_str(part, "summary", source=source, table_name="part")

    requires = optional_str_list(part, "requires", source=source, field_prefix="part.")
    conflicts = optional_str_list(part, "conflicts", source=source, field_prefix="part.")

    placeholders = data.get("placeholders", {})
    if not isinstance(placeholders, dict):
        raise SchemaError("placeholders must be a table", source=source, field="placeholders")
    placeholders_required = optional_str_list(
        placeholders, "required", source=source, field_prefix="placeholders."
    )

    raw_files = data.get("files", [])
    if not isinstance(raw_files, list):
        raise SchemaError("files must be an array of tables", source=source, field="files")
    files = tuple(
        _validate_file_rule(entry, source=source, index=i) for i, entry in enumerate(raw_files)
    )

    raw_variables = data.get("variables", {})
    if not isinstance(raw_variables, dict):
        raise SchemaError("variables must be a table", source=source, field="variables")
    for key, value in raw_variables.items():
        if not isinstance(value, str):
            raise SchemaError(
                f"variables.{key} must be a string, got {type(value).__name__}",
                source=source,
                field=f"variables.{key}",
            )
    variables: dict[str, str] = dict(raw_variables)

    return PartSchema(
        id=part_id,
        layer=layer,
        summary=summary,
        requires=requires,
        conflicts=conflicts,
        placeholders_required=placeholders_required,
        files=files,
        variables=variables,
    )


def _validate_path_safe(path: str, *, source: str, field: str) -> None:
    if path.startswith("/"):
        raise SchemaError(f"path must be relative, got {path!r}", source=source, field=field)
    if any(seg == ".." for seg in path.replace("\\", "/").split("/")):
        raise SchemaError(f"path must not contain '..', got {path!r}", source=source, field=field)


def _validate_file_rule(entry: object, *, source: str, index: int) -> FileRule:
    field_prefix = f"files[{index}]"
    if not isinstance(entry, dict):
        raise SchemaError("each [[files]] entry must be a table", source=source, field=field_prefix)
    path = require_str(entry, "path", source=source, table_name=field_prefix)
    _validate_path_safe(path, source=source, field=f"{field_prefix}.path")
    strategy = entry.get("strategy", DEFAULT_STRATEGY)
    if strategy not in STRATEGIES:
        raise SchemaError(
            f"strategy must be one of {STRATEGIES}, got {strategy!r}",
            source=source,
            field=f"{field_prefix}.strategy",
        )
    return FileRule(path=path, strategy=strategy)
