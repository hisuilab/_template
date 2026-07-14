"""Validation and immutable representation of part.toml."""

from __future__ import annotations

from dataclasses import dataclass

from template.schema._toml import optional_str_list, require_str, require_table
from template.schema.errors import SchemaError

LAYERS = ("base", "scale", "starter", "style", "lang", "languages", "features")
STRATEGIES = ("error", "replace")
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

    return PartSchema(
        id=part_id,
        layer=layer,
        summary=summary,
        requires=requires,
        conflicts=conflicts,
        placeholders_required=placeholders_required,
        files=files,
    )


def _validate_file_rule(entry: object, *, source: str, index: int) -> FileRule:
    field_prefix = f"files[{index}]"
    if not isinstance(entry, dict):
        raise SchemaError("each [[files]] entry must be a table", source=source, field=field_prefix)
    path = require_str(entry, "path", source=source, table_name=field_prefix)
    strategy = entry.get("strategy", DEFAULT_STRATEGY)
    if strategy not in STRATEGIES:
        raise SchemaError(
            f"strategy must be one of {STRATEGIES}, got {strategy!r}",
            source=source,
            field=f"{field_prefix}.strategy",
        )
    return FileRule(path=path, strategy=strategy)
