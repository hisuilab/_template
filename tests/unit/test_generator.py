"""Unit and integration tests for tooling/generator/ pipeline.

All imports below are intentionally RED until the implementation phase
creates the tooling/generator/ modules.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from tooling.generator.applier import apply, inject
from tooling.generator.errors import (
    ApplyError,
    LoadError,
    ManifestError,
    PlanError,
    RenderError,
    ResolveError,
)
from tooling.generator.loader import load_part, load_parts_for_profile, load_profile
from tooling.generator.manifest import read_manifest, write_manifest
from tooling.generator.models import (
    GenerateRequest,
    GenerationPlan,
    GenerationResult,
    InjectResult,
    LangSpec,
    ManifestData,
    PlannedFile,
)
from tooling.generator.planner import plan as make_plan
from tooling.generator.renderer import render
from tooling.generator.resolver import resolve
from template.schema.part_schema import PartSchema

TEMPLATE_ROOT = Path(__file__).resolve().parents[2] / "template"
REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


class TestLoader:
    def test_load_profile_returns_schema(self) -> None:
        profile = load_profile("starter-cli", TEMPLATE_ROOT)
        assert profile.name == "starter-cli"
        assert "base" in profile.parts

    def test_load_profile_unknown_raises_load_error(self) -> None:
        with pytest.raises(LoadError, match="no-such-profile"):
            load_profile("no-such-profile", TEMPLATE_ROOT)

    def test_load_parts_for_profile_returns_all_parts(self) -> None:
        profile = load_profile("starter-cli", TEMPLATE_ROOT)
        parts = load_parts_for_profile(profile, TEMPLATE_ROOT)
        part_ids = [p.id for p in parts]
        assert "base" in part_ids
        assert "starter/cli" in part_ids

    def test_load_parts_missing_part_raises_load_error(self, tmp_path: Path) -> None:
        from template.schema.profile_schema import ProfileSchema

        profile = ProfileSchema(
            name="ghost",
            summary="test",
            parts=("nonexistent/part",),
            variables={},
        )
        with pytest.raises(LoadError, match="nonexistent/part"):
            load_parts_for_profile(profile, tmp_path)


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------


class TestResolver:
    def test_resolve_single_part_returns_it(self) -> None:
        part = PartSchema(id="base", layer="base", summary="base part")
        result = resolve([part])
        assert result == [part]

    def test_resolve_respects_requires_order(self) -> None:
        base = PartSchema(id="base", layer="base", summary="base")
        cli = PartSchema(id="starter/cli", layer="starter", summary="cli", requires=("base",))
        result = resolve([cli, base])
        assert result.index(base) < result.index(cli)

    def test_resolve_missing_requires_raises_resolve_error(self) -> None:
        cli = PartSchema(id="starter/cli", layer="starter", summary="cli", requires=("base",))
        with pytest.raises(ResolveError, match="base"):
            resolve([cli])

    def test_resolve_circular_dependency_raises_resolve_error(self) -> None:
        a = PartSchema(id="a", layer="base", summary="a", requires=("b",))
        b = PartSchema(id="b", layer="base", summary="b", requires=("a",))
        with pytest.raises(ResolveError, match="circular"):
            resolve([a, b])

    def test_resolve_conflicting_parts_raises_resolve_error(self) -> None:
        python = PartSchema(
            id="lang/python", layer="lang", summary="python", conflicts=("lang/typescript",)
        )
        typescript = PartSchema(id="lang/typescript", layer="lang", summary="typescript")
        with pytest.raises(ResolveError, match="conflict"):
            resolve([python, typescript])

    def test_resolve_conflict_detected_regardless_of_order(self) -> None:
        python = PartSchema(
            id="lang/python", layer="lang", summary="python", conflicts=("lang/typescript",)
        )
        typescript = PartSchema(id="lang/typescript", layer="lang", summary="typescript")
        with pytest.raises(ResolveError, match="conflict"):
            resolve([typescript, python])

    def test_resolve_no_conflict_when_only_one_present(self) -> None:
        python = PartSchema(
            id="lang/python", layer="lang", summary="python", conflicts=("lang/typescript",)
        )
        result = resolve([python])
        assert result == [python]


# ---------------------------------------------------------------------------
# Planner
# ---------------------------------------------------------------------------


class TestPlanner:
    def _make_part_dir(self, base: Path, part_id: str, files: dict[str, str]) -> None:
        payload = base / "parts" / part_id / "payload"
        payload.mkdir(parents=True)
        for name, content in files.items():
            path = payload / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)

    def test_plan_strips_dot_prefix_from_filename(self, tmp_path: Path) -> None:
        self._make_part_dir(tmp_path, "base", {"dot-gitignore": "*.pyc\n"})
        part = PartSchema(id="base", layer="base", summary="base")
        req = GenerateRequest(name="myproj", profile_id="test", output_path=tmp_path / "out")
        result = make_plan(req, [part], template_root=tmp_path)
        dest_paths = [f.dest_path for f in result.files]
        assert ".gitignore" in dest_paths

    def test_plan_substitutes_project_name_in_path(self, tmp_path: Path) -> None:
        self._make_part_dir(tmp_path, "starter/library", {"src/{{project_name}}/__init__.py": ""})
        part = PartSchema(
            id="starter/library",
            layer="starter",
            summary="lib",
            placeholders_required=("project_name",),
        )
        req = GenerateRequest(name="mylib", profile_id="test", output_path=tmp_path / "out")
        result = make_plan(req, [part], template_root=tmp_path)
        dest_paths = [f.dest_path for f in result.files]
        assert "src/mylib/__init__.py" in dest_paths

    def test_plan_missing_placeholder_raises_plan_error(self, tmp_path: Path) -> None:
        self._make_part_dir(tmp_path, "starter/library", {"src/{{project_name}}/__init__.py": ""})
        part = PartSchema(
            id="starter/library",
            layer="starter",
            summary="lib",
            placeholders_required=("undeclared_var",),
        )
        req = GenerateRequest(name="mylib", profile_id="test", output_path=tmp_path / "out")
        with pytest.raises(PlanError, match="undeclared_var"):
            make_plan(req, [part], template_root=tmp_path)

    def test_plan_collision_error_strategy_raises_plan_error(self, tmp_path: Path) -> None:
        for pid in ("part_a", "part_b"):
            self._make_part_dir(tmp_path, pid, {"README.md": f"# {pid}\n"})
        part_a = PartSchema(id="part_a", layer="base", summary="a")
        part_b = PartSchema(id="part_b", layer="base", summary="b")
        req = GenerateRequest(name="x", profile_id="test", output_path=tmp_path / "out")
        with pytest.raises(PlanError, match="README.md"):
            make_plan(req, [part_a, part_b], template_root=tmp_path)

    def test_plan_add_strategy_keeps_first_part_file(self, tmp_path: Path) -> None:
        from template.schema.part_schema import FileRule

        self._make_part_dir(tmp_path, "part_a", {"shared.md": "# from a\n"})
        self._make_part_dir(tmp_path, "part_b", {"shared.md": "# from b\n"})
        part_a = PartSchema(id="part_a", layer="base", summary="a")
        part_b = PartSchema(
            id="part_b",
            layer="base",
            summary="b",
            files=(FileRule(path="shared.md", strategy="add"),),
        )
        req = GenerateRequest(name="x", profile_id="test", output_path=tmp_path / "out")
        result = make_plan(req, [part_a, part_b], template_root=tmp_path)
        shared_files = [f for f in result.files if f.dest_path == "shared.md"]
        assert len(shared_files) == 1
        assert shared_files[0].src_path.parent.parent.name == "part_a"

    def test_plan_replace_strategy_last_part_wins(self, tmp_path: Path) -> None:
        from template.schema.part_schema import FileRule

        self._make_part_dir(tmp_path, "part_a", {"README.md": "# part_a\n"})
        self._make_part_dir(tmp_path, "part_b", {"README.md": "# part_b\n"})
        part_a = PartSchema(
            id="part_a",
            layer="base",
            summary="a",
            files=(FileRule(path="README.md", strategy="replace"),),
        )
        part_b = PartSchema(
            id="part_b",
            layer="base",
            summary="b",
            files=(FileRule(path="README.md", strategy="replace"),),
        )
        req = GenerateRequest(name="x", profile_id="test", output_path=tmp_path / "out")
        result = make_plan(req, [part_a, part_b], template_root=tmp_path)
        readme_files = [f for f in result.files if f.dest_path == "README.md"]
        assert len(readme_files) == 1
        assert readme_files[0].src_path.parent.parent.name == "part_b"


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------


class TestRenderer:
    def test_render_writes_files_to_staging(self, tmp_path: Path) -> None:
        src = tmp_path / "src.txt"
        src.write_text("hello\n")
        staging = tmp_path / "staging"
        staging.mkdir()
        pfile = PlannedFile(src_path=src, dest_path="hello.txt")
        gen_plan = GenerationPlan(
            request=GenerateRequest(name="p", profile_id="t", output_path=tmp_path / "out"),
            variables={},
            files=(pfile,),
        )
        render(gen_plan, staging)
        assert (staging / "hello.txt").read_text() == "hello\n"

    def test_render_substitutes_variables_in_content(self, tmp_path: Path) -> None:
        src = tmp_path / "src.txt"
        src.write_text("project: {{project_name}}\n")
        staging = tmp_path / "staging"
        staging.mkdir()
        pfile = PlannedFile(src_path=src, dest_path="info.txt")
        gen_plan = GenerationPlan(
            request=GenerateRequest(name="myproj", profile_id="t", output_path=tmp_path / "out"),
            variables={"project_name": "myproj"},
            files=(pfile,),
        )
        render(gen_plan, staging)
        assert (staging / "info.txt").read_text() == "project: myproj\n"

    def test_render_unresolved_variable_raises_render_error(self, tmp_path: Path) -> None:
        src = tmp_path / "src.txt"
        src.write_text("{{unknown_var}}\n")
        staging = tmp_path / "staging"
        staging.mkdir()
        pfile = PlannedFile(src_path=src, dest_path="out.txt")
        gen_plan = GenerationPlan(
            request=GenerateRequest(name="p", profile_id="t", output_path=tmp_path / "out"),
            variables={},
            files=(pfile,),
        )
        with pytest.raises(RenderError, match="unknown_var"):
            render(gen_plan, staging)


# ---------------------------------------------------------------------------
# Applier
# ---------------------------------------------------------------------------


class TestApplier:
    def test_apply_copies_staging_to_output(self, tmp_path: Path) -> None:
        staging = tmp_path / "staging"
        staging.mkdir()
        (staging / "foo.txt").write_text("bar\n")
        output = tmp_path / "output"

        result = apply(staging, output)

        assert (output / "foo.txt").read_text() == "bar\n"
        assert "foo.txt" in result.files_written

    def test_apply_existing_output_raises_apply_error(self, tmp_path: Path) -> None:
        staging = tmp_path / "staging"
        staging.mkdir()
        output = tmp_path / "existing"
        output.mkdir()

        with pytest.raises(ApplyError, match="already exists"):
            apply(staging, output)

    def test_inject_adds_new_files_to_existing_dir(self, tmp_path: Path) -> None:
        staging = tmp_path / "staging"
        staging.mkdir()
        (staging / "new.txt").write_text("new\n")
        output = tmp_path / "output"
        output.mkdir()
        (output / "existing.txt").write_text("keep\n")

        result = inject(staging, output)

        assert (output / "new.txt").read_text() == "new\n"
        assert "new.txt" in result.files_added

    def test_inject_skips_files_that_already_exist(self, tmp_path: Path) -> None:
        staging = tmp_path / "staging"
        staging.mkdir()
        (staging / "existing.txt").write_text("from staging\n")
        output = tmp_path / "output"
        output.mkdir()
        (output / "existing.txt").write_text("original\n")

        result = inject(staging, output)

        assert (output / "existing.txt").read_text() == "original\n"
        assert "existing.txt" in result.files_skipped

    def test_inject_returns_result_with_added_and_skipped(self, tmp_path: Path) -> None:
        staging = tmp_path / "staging"
        staging.mkdir()
        (staging / "new.txt").write_text("new\n")
        (staging / "old.txt").write_text("overwrite attempt\n")
        output = tmp_path / "output"
        output.mkdir()
        (output / "old.txt").write_text("original\n")

        result = inject(staging, output)

        assert isinstance(result, InjectResult)
        assert "new.txt" in result.files_added
        assert "old.txt" in result.files_skipped


# ---------------------------------------------------------------------------
# Loader — load_part
# ---------------------------------------------------------------------------


class TestLoaderPart:
    def test_load_part_returns_part_schema(self) -> None:
        part = load_part("base", TEMPLATE_ROOT)
        assert part.id == "base"
        assert part.layer == "base"

    def test_load_part_unknown_raises_load_error(self) -> None:
        with pytest.raises(LoadError, match="no-such-part"):
            load_part("no-such-part", TEMPLATE_ROOT)


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


class TestManifest:
    def test_write_and_read_manifest(self, tmp_path: Path) -> None:
        parts = [
            PartSchema(id="base", layer="base", summary="base"),
            PartSchema(id="starter/cli", layer="starter", summary="cli"),
        ]
        write_manifest(tmp_path, parts, project_name="myapp")
        manifest = read_manifest(tmp_path)
        assert manifest.project_name == "myapp"
        assert "base" in manifest.applied_part_ids
        assert "starter/cli" in manifest.applied_part_ids

    def test_read_manifest_missing_raises_manifest_error(self, tmp_path: Path) -> None:
        with pytest.raises(ManifestError, match="manifest"):
            read_manifest(tmp_path)

    def test_manifest_data_applied_part_ids(self, tmp_path: Path) -> None:
        parts = [PartSchema(id="base", layer="base", summary="base")]
        write_manifest(tmp_path, parts, project_name="proj")
        manifest = read_manifest(tmp_path)
        assert isinstance(manifest, ManifestData)
        assert manifest.applied_part_ids == ("base",)

    def test_update_manifest_appends_part(self, tmp_path: Path) -> None:
        from tooling.generator.manifest import update_manifest

        parts = [PartSchema(id="base", layer="base", summary="base")]
        write_manifest(tmp_path, parts, project_name="proj")
        update_manifest(tmp_path, part_id="features/logging-python")
        manifest = read_manifest(tmp_path)
        assert "features/logging-python" in manifest.applied_part_ids

    def test_read_manifest_corrupt_toml_raises_manifest_error(self, tmp_path: Path) -> None:
        from tooling.generator.manifest import MANIFEST_FILENAME

        (tmp_path / MANIFEST_FILENAME).write_text("not valid toml ][")
        with pytest.raises(ManifestError, match="corrupt"):
            read_manifest(tmp_path)

    def test_read_manifest_schema_version_mismatch_raises_manifest_error(
        self, tmp_path: Path
    ) -> None:
        from tooling.generator.manifest import MANIFEST_FILENAME

        (tmp_path / MANIFEST_FILENAME).write_text(
            '[manifest]\nschema_version = "99"\nproject_name = "x"\ngenerated_at = "2026-01-01"\n'
        )
        with pytest.raises(ManifestError, match="schema_version"):
            read_manifest(tmp_path)

    def test_read_manifest_malformed_applied_entry_raises_manifest_error(
        self, tmp_path: Path
    ) -> None:
        from tooling.generator.manifest import MANIFEST_FILENAME

        (tmp_path / MANIFEST_FILENAME).write_text(
            '[manifest]\nschema_version = "1"\nproject_name = "x"\ngenerated_at = "2026-01-01"\n\n[[applied]]\napplied_at = "2026-01-01"\n'
        )
        with pytest.raises(ManifestError, match="malformed"):
            read_manifest(tmp_path)

    def test_update_manifest_rejects_unsafe_part_id(self, tmp_path: Path) -> None:
        from tooling.generator.manifest import update_manifest

        parts = [PartSchema(id="base", layer="base", summary="base")]
        write_manifest(tmp_path, parts, project_name="proj")
        with pytest.raises(ManifestError):
            update_manifest(tmp_path, part_id='evil"injection')


# ---------------------------------------------------------------------------
# Integration — full pipeline with real template files
# ---------------------------------------------------------------------------


class TestGeneratorIntegration:
    def test_generate_small_cli_creates_expected_files(self, tmp_path: Path) -> None:
        output = tmp_path / "foo"
        profile = load_profile("starter-cli", TEMPLATE_ROOT)
        parts = load_parts_for_profile(profile, TEMPLATE_ROOT)
        parts = resolve(parts)
        req = GenerateRequest(
            name="foo",
            profile_id="starter-cli",
            output_path=output,
            lang=(LangSpec(lang="python", role=None),),
        )
        gen_plan = make_plan(req, parts, template_root=TEMPLATE_ROOT)
        staging = tmp_path / "staging"
        staging.mkdir()
        render(gen_plan, staging)
        apply(staging, output)

        assert (output / ".gitignore").exists()
        assert (output / "flake.nix").exists()
        assert (output / "justfile").exists()
        assert (output / "src" / "main.py").exists()

    def test_generate_substitutes_project_name_in_flake_nix(self, tmp_path: Path) -> None:
        output = tmp_path / "myapp"
        profile = load_profile("starter-cli", TEMPLATE_ROOT)
        parts = load_parts_for_profile(profile, TEMPLATE_ROOT)
        parts = resolve(parts)
        req = GenerateRequest(
            name="myapp",
            profile_id="starter-cli",
            output_path=output,
            lang=(LangSpec(lang="python", role=None),),
        )
        gen_plan = make_plan(req, parts, template_root=TEMPLATE_ROOT)
        staging = tmp_path / "staging"
        staging.mkdir()
        render(gen_plan, staging)
        apply(staging, output)

        flake_content = (output / "flake.nix").read_text()
        assert "myapp" in flake_content
        assert "{{project_name}}" not in flake_content

    def test_init_workspace_rejects_workspace_with_path_separator(self, tmp_path: Path) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tooling.generator",
                "init-workspace",
                "--path",
                str(tmp_path / "out"),
                "--workspace",
                "../evil",
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode != 0
        assert "invalid" in result.stderr.lower() or "workspace" in result.stderr.lower()

    def test_generate_rejects_name_with_path_separator(self, tmp_path: Path) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tooling.generator",
                "generate",
                "--name",
                "../evil",
                "--profile",
                "starter-cli",
                "--lang",
                "python",
                "--output",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode != 0
        assert "invalid" in result.stderr.lower() or "name" in result.stderr.lower()

    def test_generate_rejects_name_with_special_chars(self, tmp_path: Path) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tooling.generator",
                "generate",
                "--name",
                "my app!",
                "--profile",
                "starter-cli",
                "--lang",
                "python",
                "--output",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode != 0

    def test_generate_via_cli_module(self, tmp_path: Path) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tooling.generator",
                "generate",
                "--name",
                "bar",
                "--profile",
                "starter-cli",
                "--output",
                str(tmp_path),
                "--lang",
                "python",
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, result.stderr
        assert (tmp_path / "bar" / ".gitignore").exists()

    def test_generate_without_lang_succeeds_for_profile_with_no_lang_parts(
        self, tmp_path: Path
    ) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tooling.generator",
                "generate",
                "--name",
                "baz",
                "--profile",
                "starter-cli",
                "--output",
                str(tmp_path),
                # No --lang argument
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        output = tmp_path / "baz"
        assert result.returncode == 0, result.stderr
        assert (output / "justfile").exists()
        assert (output / "flake.nix").exists()
        assert "baz" in (output / "flake.nix").read_text()

    def test_generate_unknown_lang_is_rejected(self, tmp_path: Path) -> None:
        result = subprocess.run(
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
                "cobol",
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode != 0
        assert "cobol" in result.stderr or "unknown" in result.stderr

    def test_generate_cli_without_output_defaults_to_name_main(self, tmp_path: Path) -> None:
        """--output absent → {cwd}/{name}/{name}-main/"""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tooling.generator",
                "generate",
                "--name",
                "myproj",
                "--profile",
                "starter-cli",
                "--lang",
                "python",
            ],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            env={
                **os.environ,
                "PYTHONPATH": str(REPO_ROOT) + ":" + os.environ.get("PYTHONPATH", ""),
            },
        )
        assert result.returncode == 0, result.stderr
        assert (tmp_path / "myproj" / "myproj-main" / ".gitignore").exists()

    def test_generate_cli_with_output_uses_it_as_parent(self, tmp_path: Path) -> None:
        """--output PARENT → PARENT/{name}/"""
        parent = tmp_path / "parent"
        parent.mkdir()
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tooling.generator",
                "generate",
                "--name",
                "myproj",
                "--profile",
                "starter-cli",
                "--lang",
                "python",
                "--output",
                str(parent),
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, result.stderr
        assert (parent / "myproj" / ".gitignore").exists()

    def test_create_cli_with_all_args_skips_wizard(self, tmp_path: Path) -> None:
        """create NAME --lang --profile → non-interactive, generates at {cwd}/{name}/{name}-main/"""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tooling.generator",
                "create",
                "myapp",
                "--lang",
                "python",
                "--profile",
                "starter-cli",
            ],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            env={
                **os.environ,
                "PYTHONPATH": str(REPO_ROOT) + ":" + os.environ.get("PYTHONPATH", ""),
            },
        )
        assert result.returncode == 0, result.stderr
        assert (tmp_path / "myapp" / "myapp-main" / ".gitignore").exists()

    def test_create_cli_with_output_uses_parent_dir(self, tmp_path: Path) -> None:
        """create NAME --output PARENT → generates at PARENT/name/ (worktree scenario)"""
        parent = tmp_path / "worktrees"
        parent.mkdir()
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tooling.generator",
                "create",
                "myapi",
                "--lang",
                "python",
                "--profile",
                "starter-cli",
                "--output",
                str(parent),
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={
                **os.environ,
                "PYTHONPATH": str(REPO_ROOT) + ":" + os.environ.get("PYTHONPATH", ""),
            },
        )
        assert result.returncode == 0, result.stderr
        assert (parent / "myapi" / ".gitignore").exists()

    def test_create_cli_invalid_lang_is_rejected(self, tmp_path: Path) -> None:
        """create NAME --lang unknown → rejected with error listing available langs"""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tooling.generator",
                "create",
                "myapp",
                "--lang",
                "cobol",
                "--profile",
                "starter-cli",
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={
                **os.environ,
                "PYTHONPATH": str(REPO_ROOT) + ":" + os.environ.get("PYTHONPATH", ""),
            },
        )
        assert result.returncode != 0
        assert "cobol" in result.stderr or "unknown" in result.stderr

    def test_create_cli_invalid_profile_is_rejected(self, tmp_path: Path) -> None:
        """create NAME --profile unknown → rejected with error listing available profiles"""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tooling.generator",
                "create",
                "myapp",
                "--lang",
                "python",
                "--profile",
                "no-such-profile",
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={
                **os.environ,
                "PYTHONPATH": str(REPO_ROOT) + ":" + os.environ.get("PYTHONPATH", ""),
            },
        )
        assert result.returncode != 0
        assert "no-such-profile" in result.stderr or "unknown" in result.stderr
