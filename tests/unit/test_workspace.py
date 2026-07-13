"""Unit tests for tooling.generator.workspace."""

from __future__ import annotations

from pathlib import Path

import pytest

from tooling.generator.workspace import init_workspace


def _make_workspace_root(base: Path) -> Path:
    ws_root = base / "workspaces"
    default = ws_root / "default"
    default.mkdir(parents=True)
    (default / "flake.nix").write_text("{ }\n")
    (default / "dot-envrc").write_text("use flake\n")
    (default / "justfile").write_text("new name:\n    echo {{name}}\n")
    return ws_root


def test_dot_prefix_stripped(tmp_path: Path) -> None:
    ws_root = _make_workspace_root(tmp_path)
    output = tmp_path / "out"

    init_workspace(
        path=output, workspace_name="default", workspace_root=ws_root, run_flake_update=False
    )

    assert (output / ".envrc").exists(), ".envrc not generated (dot- prefix not stripped)"
    assert not (output / "dot-envrc").exists(), "dot-envrc should not appear in output"


def test_all_template_files_written(tmp_path: Path) -> None:
    ws_root = _make_workspace_root(tmp_path)
    output = tmp_path / "out"

    init_workspace(
        path=output, workspace_name="default", workspace_root=ws_root, run_flake_update=False
    )

    assert (output / "flake.nix").exists()
    assert (output / ".envrc").exists()
    assert (output / "justfile").exists()


def test_unknown_workspace_name_raises(tmp_path: Path) -> None:
    ws_root = _make_workspace_root(tmp_path)
    output = tmp_path / "out"

    with pytest.raises(Exception, match="no-such-workspace"):
        init_workspace(
            path=output,
            workspace_name="no-such-workspace",
            workspace_root=ws_root,
            run_flake_update=False,
        )


def test_workspace_name_with_path_traversal_raises(tmp_path: Path) -> None:
    ws_root = _make_workspace_root(tmp_path)
    # create a directory outside workspace_root that has the traversal target name
    evil_dir = tmp_path / "evil"
    evil_dir.mkdir()
    (evil_dir / "flake.nix").write_text("evil\n")
    output = tmp_path / "out"

    with pytest.raises(Exception):
        init_workspace(
            path=output,
            workspace_name="../evil",
            workspace_root=ws_root,
            run_flake_update=False,
        )
    # output must not have been created with evil content
    assert not output.exists() or not (output / "flake.nix").exists()


def test_existing_flake_nix_raises(tmp_path: Path) -> None:
    ws_root = _make_workspace_root(tmp_path)
    output = tmp_path / "out"
    output.mkdir()
    (output / "flake.nix").write_text("existing\n")

    with pytest.raises(Exception, match="already exists"):
        init_workspace(
            path=output, workspace_name="default", workspace_root=ws_root, run_flake_update=False
        )
