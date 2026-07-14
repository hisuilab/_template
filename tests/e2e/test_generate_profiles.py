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


def _generate(name: str, profile: str, parent: Path, lang: str = "python") -> Path:
    """Generate a project into parent/name and return the output path."""
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
            "--lang",
            lang,
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert r.returncode == 0, f"generate failed:\n{r.stderr}"
    return parent / name


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
        output = _generate("myapp", "small-cli", tmp_path)
        _assert_base_files(output)

    def test_cli_src_exists(self, tmp_path: Path) -> None:
        output = _generate("myapp", "small-cli", tmp_path)
        assert (output / "src" / "main.py").exists()
        assert (output / "src" / "README.md").exists()

    def test_project_name_substituted(self, tmp_path: Path) -> None:
        output = _generate("myapp", "small-cli", tmp_path)
        assert "myapp" in (output / "flake.nix").read_text()
        assert "{{project_name}}" not in (output / "flake.nix").read_text()

    def test_rumdl_toml_present(self, tmp_path: Path) -> None:
        output = _generate("myapp", "small-cli", tmp_path)
        _assert_rumdl_toml_present(output)

    def test_check_scripts_pass(self, tmp_path: Path) -> None:
        output = _generate("myapp", "small-cli", tmp_path)
        _git_init(output)
        _assert_scripts_pass(output)


# ---------------------------------------------------------------------------
# small-web-api
# ---------------------------------------------------------------------------


class TestGenerateSmallWebApi:
    def test_base_files_exist(self, tmp_path: Path) -> None:
        output = _generate("myapi", "small-web-api", tmp_path)
        _assert_base_files(output)

    def test_web_api_src_exists(self, tmp_path: Path) -> None:
        output = _generate("myapi", "small-web-api", tmp_path)
        assert (output / "src" / "app.py").exists()
        assert (output / "src" / "routes" / "README.md").exists()

    def test_rumdl_toml_present(self, tmp_path: Path) -> None:
        output = _generate("myapi", "small-web-api", tmp_path)
        _assert_rumdl_toml_present(output)

    def test_check_scripts_pass(self, tmp_path: Path) -> None:
        output = _generate("myapi", "small-web-api", tmp_path)
        _git_init(output)
        _assert_scripts_pass(output)


# ---------------------------------------------------------------------------
# small-library
# ---------------------------------------------------------------------------


class TestGenerateSmallLibrary:
    def test_base_files_exist(self, tmp_path: Path) -> None:
        output = _generate("mylib", "small-library", tmp_path)
        _assert_base_files(output)

    def test_library_package_exists(self, tmp_path: Path) -> None:
        output = _generate("mylib", "small-library", tmp_path)
        assert (output / "src" / "mylib" / "__init__.py").exists()
        assert (output / "src" / "mylib" / "README.md").exists()
        assert (output / "CHANGELOG.md").exists()

    def test_rumdl_toml_present(self, tmp_path: Path) -> None:
        output = _generate("mylib", "small-library", tmp_path)
        _assert_rumdl_toml_present(output)

    def test_check_scripts_pass(self, tmp_path: Path) -> None:
        output = _generate("mylib", "small-library", tmp_path)
        _git_init(output)
        _assert_scripts_pass(output)


# ---------------------------------------------------------------------------
# --lang flag validation
# ---------------------------------------------------------------------------


class TestLangCli:
    def test_lang_omitted_succeeds_for_profile_without_lang_parts(self, tmp_path: Path) -> None:
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
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert r.returncode == 0, r.stderr
        assert (tmp_path / "x" / "justfile").exists()

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
                str(tmp_path),
                "--lang",
                "python,typescript",
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert r.returncode != 0

    def test_lang_python_flake_contains_python(self, tmp_path: Path) -> None:
        output = _generate("pyapp", "small-cli", tmp_path, lang="python")
        flake = (output / "flake.nix").read_text()
        assert "python" in flake

    def test_lang_typescript_flake_contains_nodejs(self, tmp_path: Path) -> None:
        output = _generate("tsapp", "small-cli", tmp_path, lang="typescript")
        flake = (output / "flake.nix").read_text()
        assert "nodejs" in flake

    def test_lang_typescript_flake_contains_biome(self, tmp_path: Path) -> None:
        output = _generate("tsapp", "small-cli", tmp_path, lang="typescript")
        flake = (output / "flake.nix").read_text()
        assert "biome" in flake

    def test_lang_typescript_treefmt_uses_biome(self, tmp_path: Path) -> None:
        output = _generate("tsapp", "small-cli", tmp_path, lang="typescript")
        treefmt = (output / "treefmt.nix").read_text()
        assert "biome" in treefmt

    def test_lang_typescript_justfile_has_lint(self, tmp_path: Path) -> None:
        output = _generate("tsapp", "small-cli", tmp_path, lang="typescript")
        justfile = (output / "justfile").read_text()
        assert "biome" in justfile

    def test_lang_typescript_biome_json_exists(self, tmp_path: Path) -> None:
        output = _generate("tsapp", "small-cli", tmp_path, lang="typescript")
        assert (output / "biome.json").exists()


# ---------------------------------------------------------------------------
# features/ai-agent: .claude/rules/dev-policy.md
# ---------------------------------------------------------------------------


class TestAiAgentPart:
    def test_claude_dev_policy_generated(self, tmp_path: Path) -> None:
        output = _generate("aiapp", "small-cli", tmp_path)
        assert (output / ".claude" / "rules" / "dev-policy.md").exists(), (
            ".claude/rules/dev-policy.md not found in generated output for small-cli profile"
        )


# ---------------------------------------------------------------------------
# features/github-rulesets: .github/rulesets/ + scripts/github-setup-rules
# ---------------------------------------------------------------------------


class TestGithubRulesetsPart:
    def _generate_with_rulesets(self, name: str, output: Path) -> None:
        """Generate using the Python API directly to inject features/github-rulesets."""
        import sys

        sys.path.insert(0, str(REPO_ROOT))
        import tempfile

        from template.schema.profile_schema import ProfileSchema
        from tooling.generator.applier import apply
        from tooling.generator.loader import load_parts_for_profile, load_profile
        from tooling.generator.models import GenerateRequest, LangSpec
        from tooling.generator.planner import plan
        from tooling.generator.renderer import render
        from tooling.generator.resolver import resolve

        template_root = REPO_ROOT / "template"
        base_profile = load_profile("small-cli", template_root)
        extended = ProfileSchema(
            name=base_profile.name,
            summary=base_profile.summary,
            parts=base_profile.parts + ("lang/python", "features/github-rulesets"),
            variables=base_profile.variables,
        )
        parts = resolve(load_parts_for_profile(extended, template_root))
        request = GenerateRequest(
            name=name,
            profile_id="small-cli",
            output_path=output,
            lang=(LangSpec(lang="python", role=None),),
        )
        gen_plan = plan(request, parts, template_root=template_root)
        with tempfile.TemporaryDirectory() as tmp:
            staging = Path(tmp) / "staging"
            staging.mkdir()
            render(gen_plan, staging)
            apply(staging, output)

    def test_rulesets_directory_generated(self, tmp_path: Path) -> None:
        output = tmp_path / "ghapp"
        self._generate_with_rulesets("ghapp", output)
        assert (output / ".github" / "rulesets").is_dir(), (
            ".github/rulesets/ not found in generated output"
        )

    def test_solo_json_generated(self, tmp_path: Path) -> None:
        output = tmp_path / "ghapp"
        self._generate_with_rulesets("ghapp", output)
        assert (output / ".github" / "rulesets" / "solo.json").exists(), (
            ".github/rulesets/solo.json not found in generated output"
        )

    def test_team_json_generated(self, tmp_path: Path) -> None:
        output = tmp_path / "ghapp"
        self._generate_with_rulesets("ghapp", output)
        assert (output / ".github" / "rulesets" / "team.json").exists(), (
            ".github/rulesets/team.json not found in generated output"
        )

    def test_github_setup_rules_script_generated(self, tmp_path: Path) -> None:
        output = tmp_path / "ghapp"
        self._generate_with_rulesets("ghapp", output)
        script = output / "scripts" / "github-setup-rules"
        assert script.exists(), "scripts/github-setup-rules not found in generated output"
        assert script.stat().st_mode & 0o111, "scripts/github-setup-rules is not executable"

    def test_rules_preset_generated(self, tmp_path: Path) -> None:
        output = tmp_path / "ghapp"
        self._generate_with_rulesets("ghapp", output)
        assert (output / ".github" / "rules-preset").exists(), (
            ".github/rules-preset not found in generated output"
        )

    def test_justfile_has_github_recipes(self, tmp_path: Path) -> None:
        output = tmp_path / "ghapp"
        self._generate_with_rulesets("ghapp", output)
        justfile = (output / "justfile").read_text()
        for recipe in [
            "github-init",
            "github-setup",
            "github-setup-rules",
            "github-status",
            "github-rules-status",
        ]:
            assert recipe in justfile, f"justfile missing recipe: {recipe}"


# ---------------------------------------------------------------------------
# features/github-rulesets: profile inclusion (small-cli / small-web-api / small-library)
# ---------------------------------------------------------------------------


class TestGithubRulesetsInProfiles:
    """Verify that github-rulesets files are present via profile inclusion (no manual injection)."""

    def test_small_cli_generates_github_rulesets(self, tmp_path: Path) -> None:
        output = _generate("myapp", "small-cli", tmp_path)
        assert (output / ".github" / "rulesets" / "solo.json").exists(), (
            "solo.json not found in small-cli generated output — "
            "add features/github-rulesets to small-cli profile parts"
        )

    def test_small_cli_generates_rules_preset(self, tmp_path: Path) -> None:
        output = _generate("myapp", "small-cli", tmp_path)
        assert (output / ".github" / "rules-preset").exists(), (
            ".github/rules-preset not found in small-cli generated output"
        )

    def test_small_cli_generates_github_setup_rules_script(self, tmp_path: Path) -> None:
        output = _generate("myapp", "small-cli", tmp_path)
        script = output / "scripts" / "github-setup-rules"
        assert script.exists(), "scripts/github-setup-rules not found in small-cli generated output"
        assert script.stat().st_mode & 0o111, "scripts/github-setup-rules is not executable"

    def test_small_web_api_generates_github_rulesets(self, tmp_path: Path) -> None:
        output = _generate("myapi", "small-web-api", tmp_path)
        assert (output / ".github" / "rulesets" / "solo.json").exists(), (
            "solo.json not found in small-web-api generated output"
        )

    def test_small_library_generates_github_rulesets(self, tmp_path: Path) -> None:
        output = _generate("mylib", "small-library", tmp_path)
        assert (output / ".github" / "rulesets" / "solo.json").exists(), (
            "solo.json not found in small-library generated output"
        )
