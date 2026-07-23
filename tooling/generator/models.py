"""Data types for the generator pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LangSpec:
    lang: str
    role: str | None


@dataclass(frozen=True)
class RoleSpec:
    """One '--role name:profile=<p>[,lang=<l>]' entry for monorepo-style generation."""

    name: str
    profile: str
    lang: str | None


@dataclass(frozen=True)
class GenerateRequest:
    name: str
    profile_id: str
    output_path: Path
    lang: tuple[LangSpec, ...] = ()


@dataclass(frozen=True)
class PlannedFile:
    src_path: Path
    dest_path: str
    strategy: str = "error"


@dataclass(frozen=True)
class GenerationPlan:
    request: GenerateRequest
    variables: dict[str, str]
    files: tuple[PlannedFile, ...]


@dataclass(frozen=True)
class GenerationResult:
    output_path: Path
    files_written: tuple[str, ...]


@dataclass(frozen=True)
class InjectResult:
    target_path: Path
    files_added: tuple[str, ...]
    files_skipped: tuple[str, ...]


@dataclass(frozen=True)
class ManifestEntry:
    part_id: str
    applied_at: str
    part_digest: str = ""
    files: tuple[str, ...] = ()


@dataclass(frozen=True)
class ManifestData:
    project_name: str
    applied_part_ids: tuple[str, ...]
    # v2 additions
    template_revision: str = ""
    generator_version: str = ""
    applied_entries: tuple[ManifestEntry, ...] = ()
