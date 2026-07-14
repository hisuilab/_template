"""E2E tests for the inject subcommand."""

from __future__ import annotations

import sys
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _generate(name: str, profile: str, parent: Path) -> Path:
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "tooling.generator",
            "generate",
            "--name",
            name,
            "--profile",
            profile,
            "--output",
            str(parent),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert r.returncode == 0, f"generate failed:\n{r.stderr}"
    return parent / name


def _inject(part: str, target: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "tooling.generator",
            "inject",
            "--part",
            part,
            "--target",
            str(target),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )


class TestInjectSubcommand:
    def test_inject_adds_new_part_files(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path)
        r = _inject("features/logging-python", output)
        assert r.returncode == 0, f"inject failed:\n{r.stderr}"
        assert (output / "src" / "logger.py").exists(), (
            "src/logger.py not found after injecting features/logging-python"
        )

    def test_inject_does_not_overwrite_existing_files(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path)
        original = (output / "justfile").read_text()
        _inject("features/logging-python", output)
        assert (output / "justfile").read_text() == original, "justfile was overwritten by inject"

    def test_inject_updates_manifest(self, tmp_path: Path) -> None:
        import tomllib

        output = _generate("myapp", "starter-cli", tmp_path)
        r = _inject("features/logging-python", output)
        assert r.returncode == 0, r.stderr
        with (output / ".template-manifest.toml").open("rb") as f:
            data = tomllib.load(f)
        applied_ids = [entry["part_id"] for entry in data.get("applied", [])]
        assert "features/logging-python" in applied_ids

    def test_inject_rejects_already_applied_part(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path)
        _inject("features/logging-python", output)
        r = _inject("features/logging-python", output)
        assert r.returncode != 0
        assert "already" in r.stderr.lower() or "applied" in r.stderr.lower()

    def test_inject_rejects_missing_manifest(self, tmp_path: Path) -> None:
        target = tmp_path / "no-manifest"
        target.mkdir()
        r = _inject("features/logging-python", target)
        assert r.returncode != 0
        assert "manifest" in r.stderr.lower()

    def test_inject_rejects_unknown_part(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path)
        r = _inject("no-such-part", output)
        assert r.returncode != 0
