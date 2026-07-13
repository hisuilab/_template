"""WORKSPACE stage: initialize a ~/Projects workspace from a fixed template."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from tooling.generator.errors import WorkspaceError

_DOT_PREFIX = "dot-"


def _strip_dot_prefix(name: str) -> str:
    if name.startswith(_DOT_PREFIX):
        return "." + name[len(_DOT_PREFIX) :]
    return name


def _default_workspace_root() -> Path:
    return Path(
        os.environ.get(
            "WORKSPACE_ROOT",
            str(Path(__file__).resolve().parents[2] / "template" / "workspaces"),
        )
    )


def init_workspace(
    path: Path,
    workspace_name: str = "default",
    workspace_root: Path | None = None,
    run_flake_update: bool = True,
) -> None:
    if workspace_root is None:
        workspace_root = _default_workspace_root()

    ws_dir = workspace_root / workspace_name

    if not ws_dir.resolve().is_relative_to(workspace_root.resolve()):
        raise WorkspaceError(
            f"invalid workspace name '{workspace_name}': must not contain path separators"
        )

    if not ws_dir.is_dir():
        available = sorted(p.name for p in workspace_root.iterdir() if p.is_dir())
        avail_str = ", ".join(available) if available else "(none)"
        raise WorkspaceError(
            f"workspace '{workspace_name}' not found in '{workspace_root}'. Available: {avail_str}"
        )

    if (path / "flake.nix").exists():
        raise WorkspaceError(f"flake.nix already exists at '{path}': will not overwrite")

    path.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    try:
        for src in sorted(ws_dir.rglob("*")):
            if not src.is_file():
                continue
            rel_parts = src.relative_to(ws_dir).parts
            stripped = tuple(_strip_dot_prefix(p) for p in rel_parts)
            dest = path.joinpath(*stripped)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            written.append(dest)
    except OSError as e:
        for f in written:
            f.unlink(missing_ok=True)
        raise WorkspaceError(f"I/O error during workspace init: {e}") from e

    if run_flake_update:
        result = subprocess.run(
            ["nix", "flake", "update", "--flake", str(path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(
                f"Warning: nix flake update failed. "
                "Run 'nix flake update' manually to generate flake.lock.",
                file=sys.stderr,
            )
