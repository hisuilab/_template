"""APPLY stage: atomic copy from staging directory to output path."""

from __future__ import annotations

import shutil
from pathlib import Path

from tooling.generator.errors import ApplyError
from tooling.generator.models import GenerationResult


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
