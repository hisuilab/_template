"""LOAD stage: deserialize profile.toml and part.toml files."""

from __future__ import annotations

import tomllib
from pathlib import Path

from template.schema.errors import SchemaError
from template.schema.part_schema import PartSchema, validate_part
from template.schema.profile_schema import ProfileSchema, validate_profile
from tooling.generator.errors import LoadError


def load_profile(profile_id: str, template_root: Path) -> ProfileSchema:
    path = template_root / "profiles" / f"{profile_id}.toml"
    if not path.exists():
        raise LoadError(f"profile '{profile_id}' not found (looked at {path})")
    with path.open("rb") as f:
        data = tomllib.load(f)
    try:
        return validate_profile(data, source=str(path))
    except SchemaError as e:
        raise LoadError(str(e)) from e


def load_part(part_id: str, template_root: Path) -> PartSchema:
    path = template_root / "parts" / part_id / "part.toml"
    if not path.exists():
        available = sorted(
            str(p.relative_to(template_root / "parts").parent)
            for p in (template_root / "parts").rglob("part.toml")
        )
        avail_str = ", ".join(available) if available else "(none)"
        raise LoadError(f"part '{part_id}' not found (looked at {path}). Available: {avail_str}")
    with path.open("rb") as f:
        data = tomllib.load(f)
    try:
        return validate_part(data, source=str(path))
    except SchemaError as e:
        raise LoadError(str(e)) from e


def load_parts_for_profile(profile: ProfileSchema, template_root: Path) -> list[PartSchema]:
    parts: list[PartSchema] = []
    for part_id in profile.parts:
        path = template_root / "parts" / part_id / "part.toml"
        if not path.exists():
            raise LoadError(f"part.toml not found for part '{part_id}' (looked at {path})")
        with path.open("rb") as f:
            data = tomllib.load(f)
        try:
            parts.append(validate_part(data, source=str(path)))
        except SchemaError as e:
            raise LoadError(str(e)) from e
    return parts
