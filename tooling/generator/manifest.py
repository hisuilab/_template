"""MANIFEST: read and write .template-manifest.toml in generated projects."""

from __future__ import annotations

import tomllib
from datetime import date
from pathlib import Path

from template.schema.part_schema import PartSchema
from tooling.generator.errors import ManifestError
from tooling.generator.models import ManifestData

MANIFEST_FILENAME = ".template-manifest.toml"
SCHEMA_VERSION = "1"

_SAFE_PART_ID_CHARS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/_-")


def _validate_part_id_for_toml(part_id: str) -> None:
    """Raise ManifestError if part_id contains characters unsafe for TOML string embedding."""
    invalid = set(part_id) - _SAFE_PART_ID_CHARS
    if invalid or ".." in part_id:
        raise ManifestError(
            f"part_id '{part_id}' contains characters not allowed in manifest: {sorted(invalid) or ['..']}"
        )


def write_manifest(project_path: Path, parts: list[PartSchema], *, project_name: str) -> None:
    today = date.today().isoformat()
    lines = [
        "[manifest]\n",
        f'schema_version = "{SCHEMA_VERSION}"\n',
        f'project_name = "{project_name}"\n',
        f'generated_at = "{today}"\n',
    ]
    for part in parts:
        _validate_part_id_for_toml(part.id)
        lines.append("\n[[applied]]\n")
        lines.append(f'part_id = "{part.id}"\n')
        lines.append(f'applied_at = "{today}"\n')
    (project_path / MANIFEST_FILENAME).write_text("".join(lines))


def read_manifest(project_path: Path) -> ManifestData:
    path = project_path / MANIFEST_FILENAME
    if not path.exists():
        raise ManifestError(
            f"manifest not found at '{path}'. Run 'generate' first to create the project."
        )
    try:
        with path.open("rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ManifestError(f"manifest at '{path}' is corrupt or invalid TOML: {e}") from e

    manifest_section = data.get("manifest", {})
    version = manifest_section.get("schema_version")
    if version != SCHEMA_VERSION:
        raise ManifestError(
            f"manifest schema_version '{version}' is not supported (expected '{SCHEMA_VERSION}'). "
            "Re-generate the project to upgrade."
        )

    project_name = manifest_section.get("project_name", "")
    try:
        applied = tuple(entry["part_id"] for entry in data.get("applied", []))
    except KeyError as e:
        raise ManifestError(
            f"manifest at '{path}' has a malformed [[applied]] entry: missing key {e}"
        ) from e
    return ManifestData(project_name=project_name, applied_part_ids=applied)


def update_manifest(project_path: Path, *, part_id: str) -> None:
    _validate_part_id_for_toml(part_id)
    path = project_path / MANIFEST_FILENAME
    if not path.exists():
        raise ManifestError(f"manifest not found at '{path}'")
    today = date.today().isoformat()
    with path.open("a") as f:
        f.write("\n[[applied]]\n")
        f.write(f'part_id = "{part_id}"\n')
        f.write(f'applied_at = "{today}"\n')
