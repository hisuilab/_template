"""E2E tests for the init-workspace subcommand."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _init_workspace(path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "tooling.generator",
            "init-workspace",
            "--path",
            str(path),
            "--no-flake-update",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )


class TestInitWorkspace:
    def test_generates_required_files(self, tmp_path: Path) -> None:
        ws = tmp_path / "ws"
        r = _init_workspace(ws)
        assert r.returncode == 0, f"init-workspace failed:\nstdout: {r.stdout}\nstderr: {r.stderr}"
        assert (ws / "flake.nix").exists(), "flake.nix not generated"
        assert (ws / ".envrc").exists(), ".envrc not generated"
        assert (ws / "justfile").exists(), "justfile not generated"

    def test_envrc_contains_use_flake(self, tmp_path: Path) -> None:
        ws = tmp_path / "ws"
        r = _init_workspace(ws)
        assert r.returncode == 0
        assert "use flake" in (ws / ".envrc").read_text()

    def test_justfile_contains_new_recipe(self, tmp_path: Path) -> None:
        ws = tmp_path / "ws"
        r = _init_workspace(ws)
        assert r.returncode == 0
        assert "new" in (ws / "justfile").read_text()

    def test_fails_if_flake_nix_exists(self, tmp_path: Path) -> None:
        ws = tmp_path / "ws"
        ws.mkdir()
        (ws / "flake.nix").write_text("existing\n")
        r = _init_workspace(ws)
        assert r.returncode != 0, "should fail when flake.nix already exists"
