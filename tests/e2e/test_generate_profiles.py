"""E2E tests for the generator pipeline across representative profiles.

Each test generates a project to a temp directory, git-initialises it so
check-readme can discover tracked files, then runs the bash verification
scripts that do not require a Nix environment.

These tests are intentionally RED until the implementation phase adds
the missing payload files (e.g. rumdl.toml).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _generate(name: str, profile: str, output: Path, lang: str = "python") -> None:
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
            str(output),
            "--lang",
            lang,
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert r.returncode == 0, f"generate failed:\n{r.stderr}"


def _git_init(path: Path) -> None:
    for cmd in [
        ["git", "init"],
        ["git", "config", "user.email", "test@test.com"],
        ["git", "config", "user.name", "Test"],
        ["git", "add", "-A"],
    ]:
        subprocess.run(cmd, cwd=str(path), capture_output=True, check=True)


def _run_script(script: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(cwd / "scripts" / script)],
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )


# ---------------------------------------------------------------------------
# Shared assertions
# ---------------------------------------------------------------------------


def _assert_base_files(output: Path) -> None:
    for rel in [".gitignore", "flake.nix", "justfile", "LICENSE", "README.md", "treefmt.nix"]:
        assert (output / rel).exists(), f"missing base file: {rel}"


def _assert_scripts_pass(output: Path) -> None:
    for script in ["check-readme", "check-status", "check-encoding"]:
        r = _run_script(script, output)
        assert r.returncode == 0, f"{script} failed:\nstdout: {r.stdout}\nstderr: {r.stderr}"


def _assert_rumdl_toml_present(output: Path) -> None:
    assert (output / "rumdl.toml").exists(), (
        "rumdl.toml is missing from the generated project. "
        "Add it to template/parts/base/payload/rumdl.toml"
    )


# ---------------------------------------------------------------------------
# small-cli
# ---------------------------------------------------------------------------


class TestGenerateSmallCli:
    def test_base_files_exist(self, tmp_path: Path) -> None:
        output = tmp_path / "myapp"
        _generate("myapp", "small-cli", output)
        _assert_base_files(output)

    def test_cli_src_exists(self, tmp_path: Path) -> None:
        output = tmp_path / "myapp"
        _generate("myapp", "small-cli", output)
        assert (output / "src" / "main.py").exists()
        assert (output / "src" / "README.md").exists()

    def test_project_name_substituted(self, tmp_path: Path) -> None:
        output = tmp_path / "myapp"
        _generate("myapp", "small-cli", output)
        assert "myapp" in (output / "flake.nix").read_text()
        assert "{{project_name}}" not in (output / "flake.nix").read_text()

    def test_rumdl_toml_present(self, tmp_path: Path) -> None:
        output = tmp_path / "myapp"
        _generate("myapp", "small-cli", output)
        _assert_rumdl_toml_present(output)

    def test_check_scripts_pass(self, tmp_path: Path) -> None:
        output = tmp_path / "myapp"
        _generate("myapp", "small-cli", output)
        _git_init(output)
        _assert_scripts_pass(output)


# ---------------------------------------------------------------------------
# small-web-api
# ---------------------------------------------------------------------------


class TestGenerateSmallWebApi:
    def test_base_files_exist(self, tmp_path: Path) -> None:
        output = tmp_path / "myapi"
        _generate("myapi", "small-web-api", output)
        _assert_base_files(output)

    def test_web_api_src_exists(self, tmp_path: Path) -> None:
        output = tmp_path / "myapi"
        _generate("myapi", "small-web-api", output)
        assert (output / "src" / "app.py").exists()
        assert (output / "src" / "routes" / "README.md").exists()

    def test_rumdl_toml_present(self, tmp_path: Path) -> None:
        output = tmp_path / "myapi"
        _generate("myapi", "small-web-api", output)
        _assert_rumdl_toml_present(output)

    def test_check_scripts_pass(self, tmp_path: Path) -> None:
        output = tmp_path / "myapi"
        _generate("myapi", "small-web-api", output)
        _git_init(output)
        _assert_scripts_pass(output)


# ---------------------------------------------------------------------------
# small-library
# ---------------------------------------------------------------------------


class TestGenerateSmallLibrary:
    def test_base_files_exist(self, tmp_path: Path) -> None:
        output = tmp_path / "mylib"
        _generate("mylib", "small-library", output)
        _assert_base_files(output)

    def test_library_package_exists(self, tmp_path: Path) -> None:
        output = tmp_path / "mylib"
        _generate("mylib", "small-library", output)
        assert (output / "src" / "mylib" / "__init__.py").exists()
        assert (output / "src" / "mylib" / "README.md").exists()
        assert (output / "CHANGELOG.md").exists()

    def test_rumdl_toml_present(self, tmp_path: Path) -> None:
        output = tmp_path / "mylib"
        _generate("mylib", "small-library", output)
        _assert_rumdl_toml_present(output)

    def test_check_scripts_pass(self, tmp_path: Path) -> None:
        output = tmp_path / "mylib"
        _generate("mylib", "small-library", output)
        _git_init(output)
        _assert_scripts_pass(output)


# ---------------------------------------------------------------------------
# --lang flag validation
# ---------------------------------------------------------------------------


class TestLangCli:
    def test_lang_required_error(self, tmp_path: Path) -> None:
        r = subprocess.run(
            [
                sys.executable,
                "-m",
                "tooling.generator",
                "generate",
                "--name",
                "x",
                "--profile",
                "small-cli",
                "--output",
                str(tmp_path / "out"),
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert r.returncode != 0
        combined = r.stdout + r.stderr
        assert "lang" in combined.lower()

    def test_lang_multiple_error(self, tmp_path: Path) -> None:
        r = subprocess.run(
            [
                sys.executable,
                "-m",
                "tooling.generator",
                "generate",
                "--name",
                "x",
                "--profile",
                "small-cli",
                "--output",
                str(tmp_path / "out"),
                "--lang",
                "python,typescript",
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert r.returncode != 0

    def test_lang_python_flake_contains_python(self, tmp_path: Path) -> None:
        output = tmp_path / "pyapp"
        _generate("pyapp", "small-cli", output, lang="python")
        flake = (output / "flake.nix").read_text()
        assert "python" in flake

    def test_lang_typescript_flake_contains_nodejs(self, tmp_path: Path) -> None:
        output = tmp_path / "tsapp"
        _generate("tsapp", "small-cli", output, lang="typescript")
        flake = (output / "flake.nix").read_text()
        assert "nodejs" in flake

    def test_lang_typescript_flake_contains_biome(self, tmp_path: Path) -> None:
        output = tmp_path / "tsapp"
        _generate("tsapp", "small-cli", output, lang="typescript")
        flake = (output / "flake.nix").read_text()
        assert "biome" in flake

    def test_lang_typescript_treefmt_uses_biome(self, tmp_path: Path) -> None:
        output = tmp_path / "tsapp"
        _generate("tsapp", "small-cli", output, lang="typescript")
        treefmt = (output / "treefmt.nix").read_text()
        assert "biome" in treefmt

    def test_lang_typescript_justfile_has_lint(self, tmp_path: Path) -> None:
        output = tmp_path / "tsapp"
        _generate("tsapp", "small-cli", output, lang="typescript")
        justfile = (output / "justfile").read_text()
        assert "biome" in justfile
