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


def write_manifest(project_path: Path, parts: list[PartSchema], *, project_name: str) -> None:
    today = date.today().isoformat()
    lines = [
        "[manifest]\n",
        f'schema_version = "{SCHEMA_VERSION}"\n',
        f'project_name = "{project_name}"\n',
        f'generated_at = "{today}"\n',
    ]
    for part in parts:
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
    with path.open("rb") as f:
        data = tomllib.load(f)
    project_name = data.get("manifest", {}).get("project_name", "")
    applied = tuple(entry["part_id"] for entry in data.get("applied", []))
    return ManifestData(project_name=project_name, applied_part_ids=applied)


def update_manifest(project_path: Path, *, part_id: str) -> None:
    path = project_path / MANIFEST_FILENAME
    if not path.exists():
        raise ManifestError(f"manifest not found at '{path}'")
    today = date.today().isoformat()
    with path.open("a") as f:
        f.write("\n[[applied]]\n")
        f.write(f'part_id = "{part_id}"\n')
        f.write(f'applied_at = "{today}"\n')
