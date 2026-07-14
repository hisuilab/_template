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
# starter-cli
# ---------------------------------------------------------------------------


class TestGenerateStarterCli:
    def test_base_files_exist(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path)
        _assert_base_files(output)

    def test_cli_src_exists(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path)
        assert (output / "src" / "main.py").exists()
        assert (output / "src" / "README.md").exists()

    def test_project_name_substituted(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path)
        assert "myapp" in (output / "flake.nix").read_text()
        assert "{{project_name}}" not in (output / "flake.nix").read_text()

    def test_rumdl_toml_present(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path)
        _assert_rumdl_toml_present(output)

    def test_check_scripts_pass(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path)
        _git_init(output)
        _assert_scripts_pass(output)


# ---------------------------------------------------------------------------
# starter-web-api
# ---------------------------------------------------------------------------


class TestGenerateStarterWebApi:
    def test_base_files_exist(self, tmp_path: Path) -> None:
        output = _generate("myapi", "starter-web-api", tmp_path)
        _assert_base_files(output)

    def test_web_api_src_exists(self, tmp_path: Path) -> None:
        output = _generate("myapi", "starter-web-api", tmp_path)
        assert (output / "src" / "app.py").exists()
        assert (output / "src" / "routes" / "README.md").exists()

    def test_rumdl_toml_present(self, tmp_path: Path) -> None:
        output = _generate("myapi", "starter-web-api", tmp_path)
        _assert_rumdl_toml_present(output)

    def test_check_scripts_pass(self, tmp_path: Path) -> None:
        output = _generate("myapi", "starter-web-api", tmp_path)
        _git_init(output)
        _assert_scripts_pass(output)


# ---------------------------------------------------------------------------
# starter-library
# ---------------------------------------------------------------------------


class TestGenerateStarterLibrary:
    def test_base_files_exist(self, tmp_path: Path) -> None:
        output = _generate("mylib", "starter-library", tmp_path)
        _assert_base_files(output)

    def test_library_package_exists(self, tmp_path: Path) -> None:
        output = _generate("mylib", "starter-library", tmp_path)
        assert (output / "src" / "mylib" / "__init__.py").exists()
        assert (output / "src" / "mylib" / "README.md").exists()
        assert (output / "CHANGELOG.md").exists()

    def test_rumdl_toml_present(self, tmp_path: Path) -> None:
        output = _generate("mylib", "starter-library", tmp_path)
        _assert_rumdl_toml_present(output)

    def test_check_scripts_pass(self, tmp_path: Path) -> None:
        output = _generate("mylib", "starter-library", tmp_path)
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
                "starter-cli",
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
                "starter-cli",
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
        output = _generate("pyapp", "starter-cli", tmp_path, lang="python")
        flake = (output / "flake.nix").read_text()
        assert "python" in flake

    def test_lang_typescript_flake_contains_nodejs(self, tmp_path: Path) -> None:
        output = _generate("tsapp", "starter-cli", tmp_path, lang="typescript")
        flake = (output / "flake.nix").read_text()
        assert "nodejs" in flake

    def test_lang_typescript_flake_contains_biome(self, tmp_path: Path) -> None:
        output = _generate("tsapp", "starter-cli", tmp_path, lang="typescript")
        flake = (output / "flake.nix").read_text()
        assert "biome" in flake

    def test_lang_typescript_treefmt_uses_biome(self, tmp_path: Path) -> None:
        output = _generate("tsapp", "starter-cli", tmp_path, lang="typescript")
        treefmt = (output / "treefmt.nix").read_text()
        assert "biome" in treefmt

    def test_lang_typescript_justfile_has_lint(self, tmp_path: Path) -> None:
        output = _generate("tsapp", "starter-cli", tmp_path, lang="typescript")
        justfile = (output / "justfile").read_text()
        assert "biome" in justfile

    def test_lang_typescript_biome_json_exists(self, tmp_path: Path) -> None:
        output = _generate("tsapp", "starter-cli", tmp_path, lang="typescript")
        assert (output / "biome.json").exists()


# ---------------------------------------------------------------------------
# features/ai-agent: .claude/rules/dev-policy.md
# ---------------------------------------------------------------------------


class TestGenerateManifest:
    def test_generate_creates_manifest(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path)
        assert (output / ".template-manifest.toml").exists(), (
            ".template-manifest.toml not found after generate"
        )

    def test_manifest_contains_project_name(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path)
        import tomllib

        with (output / ".template-manifest.toml").open("rb") as f:
            data = tomllib.load(f)
        assert data["manifest"]["project_name"] == "myapp"

    def test_manifest_contains_applied_parts(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path)
        import tomllib

        with (output / ".template-manifest.toml").open("rb") as f:
            data = tomllib.load(f)
        applied_ids = [entry["part_id"] for entry in data.get("applied", [])]
        assert "base" in applied_ids
        assert "starter/cli" in applied_ids


class TestAiAgentPart:
    def test_claude_dev_policy_generated(self, tmp_path: Path) -> None:
        output = _generate("aiapp", "starter-cli", tmp_path)
        assert (output / ".claude" / "rules" / "dev-policy.md").exists(), (
            ".claude/rules/dev-policy.md not found in generated output for starter-cli profile"
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
        base_profile = load_profile("starter-cli", template_root)
        extended = ProfileSchema(
            name=base_profile.name,
            summary=base_profile.summary,
            parts=base_profile.parts + ("lang/python", "features/github-rulesets"),
            variables=base_profile.variables,
        )
        parts = resolve(load_parts_for_profile(extended, template_root))
        request = GenerateRequest(
            name=name,
            profile_id="starter-cli",
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
# features/github-rulesets: profile inclusion (starter-cli / starter-web-api / starter-library)
# ---------------------------------------------------------------------------


class TestGithubRulesetsInProfiles:
    """Verify that github-rulesets files are present via profile inclusion (no manual injection)."""

    def test_starter_cli_generates_github_rulesets(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path)
        assert (output / ".github" / "rulesets" / "solo.json").exists(), (
            "solo.json not found in starter-cli generated output — "
            "add features/github-rulesets to starter-cli profile parts"
        )

    def test_starter_cli_generates_rules_preset(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path)
        assert (output / ".github" / "rules-preset").exists(), (
            ".github/rules-preset not found in starter-cli generated output"
        )

    def test_starter_cli_generates_github_setup_rules_script(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path)
        script = output / "scripts" / "github-setup-rules"
        assert script.exists(), (
            "scripts/github-setup-rules not found in starter-cli generated output"
        )
        assert script.stat().st_mode & 0o111, "scripts/github-setup-rules is not executable"

    def test_starter_web_api_generates_github_rulesets(self, tmp_path: Path) -> None:
        output = _generate("myapi", "starter-web-api", tmp_path)
        assert (output / ".github" / "rulesets" / "solo.json").exists(), (
            "solo.json not found in starter-web-api generated output"
        )

    def test_starter_library_generates_github_rulesets(self, tmp_path: Path) -> None:
        output = _generate("mylib", "starter-library", tmp_path)
        assert (output / ".github" / "rulesets" / "solo.json").exists(), (
            "solo.json not found in starter-library generated output"
        )


# ---------------------------------------------------------------------------
# features/github-project: profile inclusion (starter-cli / starter-web-api / starter-library)
# ---------------------------------------------------------------------------


class TestGithubProjectInProfiles:
    """Verify that github-project files are present via profile inclusion."""

    def test_starter_cli_generates_pr_template(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path)
        assert (output / ".github" / "PULL_REQUEST_TEMPLATE.md").exists(), (
            "PULL_REQUEST_TEMPLATE.md not found — add features/github-project to starter-cli profile"
        )

    def test_starter_cli_generates_bug_report_template(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path)
        assert (output / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml").exists(), (
            "ISSUE_TEMPLATE/bug_report.yml not found in starter-cli generated output"
        )

    def test_starter_cli_generates_feature_request_template(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path)
        assert (output / ".github" / "ISSUE_TEMPLATE" / "feature_request.yml").exists(), (
            "ISSUE_TEMPLATE/feature_request.yml not found in starter-cli generated output"
        )

    def test_starter_cli_generates_task_template(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path)
        assert (output / ".github" / "ISSUE_TEMPLATE" / "task.yml").exists(), (
            "ISSUE_TEMPLATE/task.yml not found in starter-cli generated output"
        )

    def test_starter_cli_generates_issue_template_config(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path)
        assert (output / ".github" / "ISSUE_TEMPLATE" / "config.yml").exists(), (
            "ISSUE_TEMPLATE/config.yml not found in starter-cli generated output"
        )

    def test_starter_cli_generates_ci_workflow(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path)
        assert (output / ".github" / "workflows" / "ci.yml").exists(), (
            ".github/workflows/ci.yml not found in starter-cli generated output"
        )

    def test_starter_cli_generates_update_flake_workflow(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path)
        assert (output / ".github" / "workflows" / "update-flake.yml").exists(), (
            ".github/workflows/update-flake.yml not found in starter-cli generated output"
        )

    def test_starter_cli_generates_dependabot(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path)
        assert (output / ".github" / "dependabot.yml").exists(), (
            ".github/dependabot.yml not found in starter-cli generated output"
        )

    def test_starter_cli_generates_codeowners(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path)
        assert (output / ".github" / "CODEOWNERS").exists(), (
            ".github/CODEOWNERS not found in starter-cli generated output"
        )

    def test_project_name_substituted_in_bug_report(self, tmp_path: Path) -> None:
        output = _generate("myapp", "starter-cli", tmp_path)
        content = (output / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml").read_text()
        assert "myapp" in content, "project_name not substituted in bug_report.yml"
        assert "{{project_name}}" not in content, "{{project_name}} placeholder not replaced"

    def test_starter_web_api_generates_github_project(self, tmp_path: Path) -> None:
        output = _generate("myapi", "starter-web-api", tmp_path)
        assert (output / ".github" / "PULL_REQUEST_TEMPLATE.md").exists(), (
            "PULL_REQUEST_TEMPLATE.md not found in starter-web-api generated output"
        )

    def test_starter_library_generates_github_project(self, tmp_path: Path) -> None:
        output = _generate("mylib", "starter-library", tmp_path)
        assert (output / ".github" / "PULL_REQUEST_TEMPLATE.md").exists(), (
            "PULL_REQUEST_TEMPLATE.md not found in starter-library generated output"
        )
