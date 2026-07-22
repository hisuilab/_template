"""E2E tests for the inject subcommand."""

from __future__ import annotations

import sys
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _generate(name: str, profile: str, parent: Path, lang: str | None = None) -> Path:
    cmd = [
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
    ]
    if lang is not None:
        cmd += ["--lang", lang]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
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
        output = _generate("myapp", "starter-cli", tmp_path, lang="python")
        r = _inject("features/logging-python", output)
        assert r.returncode == 0, f"inject failed:\n{r.stderr}"
        assert (output / "src" / "logger.py").exists(), (
            "src/logger.py not found after injecting features/logging-python"
        )

    def test_inject_does_not_overwrite_existing_files(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path, lang="python")
        original = (output / "justfile").read_text()
        _inject("features/logging-python", output)
        assert (output / "justfile").read_text() == original, "justfile was overwritten by inject"

    def test_inject_updates_manifest(self, tmp_path: Path) -> None:
        import tomllib

        output = _generate("myapp", "starter-cli", tmp_path, lang="python")
        r = _inject("features/logging-python", output)
        assert r.returncode == 0, r.stderr
        with (output / ".template-manifest.toml").open("rb") as f:
            data = tomllib.load(f)
        applied_ids = [entry["part_id"] for entry in data.get("applied", [])]
        assert "features/logging-python" in applied_ids

    def test_inject_rejects_already_applied_part(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path, lang="python")
        _inject("features/logging-python", output)
        r = _inject("features/logging-python", output)
        assert r.returncode != 0
        assert "already" in r.stderr.lower() or "applied" in r.stderr.lower()

    def test_inject_rejects_logging_python_without_lang_python(self, tmp_path: Path) -> None:
        # features/logging-python ships a .py file; without lang/python present,
        # the project's .gitignore has no __pycache__/ entry (issue #94). This
        # must be rejected rather than silently leaking untracked cache dirs.
        output = _generate("myapp", "starter-cli", tmp_path)
        r = _inject("features/logging-python", output)
        assert r.returncode != 0
        assert "lang/python" in r.stderr

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
        assert "not found" in r.stderr.lower() or "available" in r.stderr.lower()

    def test_inject_rejects_conflicting_part(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path, lang="python")
        r = _inject("lang/typescript", output)
        assert r.returncode != 0
        assert "conflicts" in r.stderr.lower()

    def test_inject_rejects_missing_requires(self, tmp_path: Path) -> None:
        # Write a manifest that doesn't include "base" so requires check fails
        target = tmp_path / "partial-project"
        target.mkdir()
        (target / ".template-manifest.toml").write_text(
            '[manifest]\nschema_version = "1"\nproject_name = "partial"\ngenerated_at = "2026-01-01"\n'
        )
        r = _inject("features/logging-python", target)
        assert r.returncode != 0
        assert "required" in r.stderr.lower() or "requires" in r.stderr.lower()

    def test_inject_all_skip_does_not_update_manifest(self, tmp_path: Path) -> None:
        """全ファイルが既存でskipの場合、manifest に Part を記録しないことを確認します。"""
        import tomllib

        output = _generate("myapp", "starter-cli", tmp_path, lang="python")
        # logging-python のファイルを手動で配置してすべてskipさせる
        (output / "src" / "logger.py").write_text("# pre-existing\n")
        r = _inject("features/logging-python", output)
        assert r.returncode == 0, r.stderr
        with (output / ".template-manifest.toml").open("rb") as f:
            data = tomllib.load(f)
        applied_ids = [entry["part_id"] for entry in data.get("applied", [])]
        assert "features/logging-python" not in applied_ids, (
            "manifest should NOT record part when all files were skipped"
        )

    def test_inject_all_skip_allows_retry(self, tmp_path: Path) -> None:
        """全skipでmanifest未記録の場合、再実行が可能であることを確認します。"""
        output = _generate("myapp", "starter-cli", tmp_path, lang="python")
        (output / "src" / "logger.py").write_text("# pre-existing\n")
        r1 = _inject("features/logging-python", output)
        assert r1.returncode == 0, r1.stderr
        # 再実行できる（already applied と弾かれない）
        r2 = _inject("features/logging-python", output)
        assert r2.returncode == 0, f"retry should succeed but got: {r2.stderr}"
