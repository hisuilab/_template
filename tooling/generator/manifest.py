"""MANIFEST: read and write .template-manifest.toml in generated projects."""

from __future__ import annotations

import tomllib
from datetime import date
from pathlib import Path

from template.schema.part_schema import PartSchema
from tooling.generator.errors import ManifestError
from tooling.generator.models import ManifestData, ManifestEntry

MANIFEST_FILENAME = ".template-manifest.toml"
SCHEMA_VERSION = "2"

_SAFE_PART_ID_CHARS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/_-")


def _validate_part_id_for_toml(part_id: str) -> None:
    """Raise ManifestError if part_id contains characters unsafe for TOML string embedding."""
    invalid = set(part_id) - _SAFE_PART_ID_CHARS
    if invalid or ".." in part_id:
        raise ManifestError(
            f"part_id '{part_id}' contains characters not allowed in manifest: {sorted(invalid) or ['..']}"
        )


def _escape_toml_str(value: str) -> str:
    """Escape a string for embedding in a TOML double-quoted string."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _format_files_list(files: list[str] | tuple[str, ...]) -> str:
    """Format a list of file paths as a TOML inline array."""
    items = ", ".join(f'"{_escape_toml_str(f)}"' for f in files)
    return f"[{items}]"


def _atomic_write(path: Path, content: str) -> None:
    """Write content to path atomically via a .tmp file then rename."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _serialize_manifest(
    project_name: str,
    today: str,
    template_revision: str,
    generator_version: str,
    entries: list[tuple[str, str, str, list[str]]],
) -> str:
    """Serialize manifest to TOML string.

    entries: list of (part_id, applied_at, part_digest, files)
    """
    lines = [
        "[manifest]\n",
        f'schema_version = "{SCHEMA_VERSION}"\n',
        f'project_name = "{_escape_toml_str(project_name)}"\n',
        f'generated_at = "{today}"\n',
        f'template_revision = "{_escape_toml_str(template_revision)}"\n',
        f'generator_version = "{_escape_toml_str(generator_version)}"\n',
    ]
    for part_id, applied_at, part_digest, files in entries:
        lines.append("\n[[applied]]\n")
        lines.append(f'part_id = "{_escape_toml_str(part_id)}"\n')
        lines.append(f'applied_at = "{applied_at}"\n')
        lines.append(f'part_digest = "{_escape_toml_str(part_digest)}"\n')
        lines.append(f"files = {_format_files_list(files)}\n")
    return "".join(lines)


def write_manifest(
    project_path: Path,
    parts: list[PartSchema],
    *,
    project_name: str,
    files_by_part: dict[str, list[str]] | None = None,
    template_revision: str = "",
    generator_version: str = "",
    part_digests: dict[str, str] | None = None,
) -> None:
    today = date.today().isoformat()
    for part in parts:
        _validate_part_id_for_toml(part.id)

    entries: list[tuple[str, str, str, list[str]]] = []
    for part in parts:
        digest = (part_digests or {}).get(part.id, "")
        files = (files_by_part or {}).get(part.id, [])
        entries.append((part.id, today, digest, files))

    content = _serialize_manifest(
        project_name=project_name,
        today=today,
        template_revision=template_revision,
        generator_version=generator_version,
        entries=entries,
    )
    _atomic_write(project_path / MANIFEST_FILENAME, content)


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
    template_revision = manifest_section.get("template_revision", "")
    generator_version = manifest_section.get("generator_version", "")

    raw_applied = data.get("applied", [])
    seen_ids: set[str] = set()
    applied_entries: list[ManifestEntry] = []
    for entry in raw_applied:
        try:
            part_id = entry["part_id"]
        except KeyError as e:
            raise ManifestError(
                f"manifest at '{path}' has a malformed [[applied]] entry: missing key {e}"
            ) from e
        if part_id in seen_ids:
            raise ManifestError(f"manifest at '{path}' has duplicate part_id '{part_id}'")
        seen_ids.add(part_id)
        applied_at = entry.get("applied_at", "")
        part_digest = entry.get("part_digest", "")
        files_raw = entry.get("files", [])
        if not isinstance(files_raw, list) or not all(isinstance(f, str) for f in files_raw):
            raise ManifestError(
                f"manifest at '{path}': [[applied]] entry '{part_id}' has invalid 'files' field "
                "(expected list of strings)"
            )
        applied_entries.append(
            ManifestEntry(
                part_id=part_id,
                applied_at=applied_at,
                part_digest=part_digest,
                files=tuple(files_raw),
            )
        )

    applied_part_ids = tuple(e.part_id for e in applied_entries)
    return ManifestData(
        project_name=project_name,
        applied_part_ids=applied_part_ids,
        template_revision=template_revision,
        generator_version=generator_version,
        applied_entries=tuple(applied_entries),
    )


def update_manifest(
    project_path: Path,
    *,
    part_id: str,
    files: list[str] | None = None,
    part_digest: str = "",
) -> None:
    _validate_part_id_for_toml(part_id)
    path = project_path / MANIFEST_FILENAME
    if not path.exists():
        raise ManifestError(f"manifest not found at '{path}'")

    # Re-read raw TOML to preserve generated_at and other header fields
    try:
        with path.open("rb") as f:
            raw = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ManifestError(f"manifest at '{path}' is corrupt or invalid TOML: {e}") from e

    manifest_section = raw.get("manifest", {})
    version = manifest_section.get("schema_version")
    if version != SCHEMA_VERSION:
        raise ManifestError(
            f"manifest schema_version '{version}' is not supported (expected '{SCHEMA_VERSION}'). "
            "Re-generate the project to upgrade."
        )

    project_name = manifest_section.get("project_name", "")
    generated_at = manifest_section.get("generated_at", date.today().isoformat())
    template_revision = manifest_section.get("template_revision", "")
    generator_version = manifest_section.get("generator_version", "")

    today = date.today().isoformat()
    existing_entries: list[tuple[str, str, str, list[str]]] = []
    for entry in raw.get("applied", []):
        try:
            eid = entry["part_id"]
        except KeyError as e:
            raise ManifestError(
                f"manifest at '{path}' has a malformed [[applied]] entry: missing key {e}"
            ) from e
        existing_entries.append(
            (eid, entry.get("applied_at", ""), entry.get("part_digest", ""), entry.get("files", []))
        )
    existing_entries.append((part_id, today, part_digest, files or []))

    content = _serialize_manifest(
        project_name=project_name,
        today=generated_at,
        template_revision=template_revision,
        generator_version=generator_version,
        entries=existing_entries,
    )
    _atomic_write(path, content)
