"""APPLY stage: atomic copy from staging directory to output path."""

from __future__ import annotations

import shutil
from pathlib import Path

from tooling.generator.errors import ApplyError
from tooling.generator.models import GenerationResult, InjectResult


def apply(staging_dir: Path, output_path: Path) -> GenerationResult:
    if output_path.exists():
        raise ApplyError(f"output path already exists: '{output_path}'")

    files_written: list[str] = []
    try:
        for src in sorted(staging_dir.rglob("*")):
            if not src.is_file():
                continue
            rel = str(src.relative_to(staging_dir))
            dest = output_path / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            files_written.append(rel)
    except OSError as e:
        if output_path.exists():
            shutil.rmtree(output_path, ignore_errors=True)
        raise ApplyError(f"I/O error during apply: {e}") from e

    return GenerationResult(output_path=output_path, files_written=tuple(files_written))


def inject(staging_dir: Path, target_path: Path) -> InjectResult:
    files_added: list[str] = []
    files_skipped: list[str] = []
    try:
        for src in sorted(staging_dir.rglob("*")):
            if not src.is_file():
                continue
            rel = str(src.relative_to(staging_dir))
            dest = target_path / rel
            if dest.exists():
                files_skipped.append(rel)
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            files_added.append(rel)
    except OSError as e:
        for rel in files_added:
            (target_path / rel).unlink(missing_ok=True)
        raise ApplyError(f"I/O error during inject: {e}") from e

    return InjectResult(
        target_path=target_path,
        files_added=tuple(files_added),
        files_skipped=tuple(files_skipped),
    )
