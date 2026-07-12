"""Unit and integration tests for tooling/generator/ pipeline.

All imports below are intentionally RED until the implementation phase
creates the tooling/generator/ modules.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from tooling.generator.applier import apply
from tooling.generator.errors import ApplyError, LoadError, PlanError, RenderError, ResolveError
from tooling.generator.loader import load_parts_for_profile, load_profile
from tooling.generator.models import GenerateRequest, GenerationPlan, GenerationResult, PlannedFile
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
        profile = load_profile("small-cli", TEMPLATE_ROOT)
        assert profile.name == "small-cli"
        assert "base" in profile.parts

    def test_load_profile_unknown_raises_load_error(self) -> None:
        with pytest.raises(LoadError, match="no-such-profile"):
            load_profile("no-such-profile", TEMPLATE_ROOT)

    def test_load_parts_for_profile_returns_all_parts(self) -> None:
        profile = load_profile("small-cli", TEMPLATE_ROOT)
        parts = load_parts_for_profile(profile, TEMPLATE_ROOT)
        part_ids = [p.id for p in parts]
        assert "base" in part_ids
        assert "purpose/cli" in part_ids

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
        cli = PartSchema(id="purpose/cli", layer="purpose", summary="cli", requires=("base",))
        result = resolve([cli, base])
        assert result.index(base) < result.index(cli)

    def test_resolve_missing_requires_raises_resolve_error(self) -> None:
        cli = PartSchema(id="purpose/cli", layer="purpose", summary="cli", requires=("base",))
        with pytest.raises(ResolveError, match="base"):
            resolve([cli])

    def test_resolve_circular_dependency_raises_resolve_error(self) -> None:
        a = PartSchema(id="a", layer="base", summary="a", requires=("b",))
        b = PartSchema(id="b", layer="base", summary="b", requires=("a",))
        with pytest.raises(ResolveError, match="circular"):
            resolve([a, b])


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
        self._make_part_dir(tmp_path, "purpose/library", {"src/{{project_name}}/__init__.py": ""})
        part = PartSchema(
            id="purpose/library",
            layer="purpose",
            summary="lib",
            placeholders_required=("project_name",),
        )
        req = GenerateRequest(name="mylib", profile_id="test", output_path=tmp_path / "out")
        result = make_plan(req, [part], template_root=tmp_path)
        dest_paths = [f.dest_path for f in result.files]
        assert "src/mylib/__init__.py" in dest_paths

    def test_plan_missing_placeholder_raises_plan_error(self, tmp_path: Path) -> None:
        self._make_part_dir(tmp_path, "purpose/library", {"src/{{project_name}}/__init__.py": ""})
        part = PartSchema(
            id="purpose/library",
            layer="purpose",
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


# ---------------------------------------------------------------------------
# Integration — full pipeline with real template files
# ---------------------------------------------------------------------------


class TestGeneratorIntegration:
    def test_generate_small_cli_creates_expected_files(self, tmp_path: Path) -> None:
        output = tmp_path / "foo"
        profile = load_profile("small-cli", TEMPLATE_ROOT)
        parts = load_parts_for_profile(profile, TEMPLATE_ROOT)
        parts = resolve(parts)
        req = GenerateRequest(name="foo", profile_id="small-cli", output_path=output)
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
        profile = load_profile("small-cli", TEMPLATE_ROOT)
        parts = load_parts_for_profile(profile, TEMPLATE_ROOT)
        parts = resolve(parts)
        req = GenerateRequest(name="myapp", profile_id="small-cli", output_path=output)
        gen_plan = make_plan(req, parts, template_root=TEMPLATE_ROOT)
        staging = tmp_path / "staging"
        staging.mkdir()
        render(gen_plan, staging)
        apply(staging, output)

        flake_content = (output / "flake.nix").read_text()
        assert "myapp" in flake_content
        assert "{{project_name}}" not in flake_content

    def test_generate_via_cli_module(self, tmp_path: Path) -> None:
        output = tmp_path / "bar"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tooling.generator",
                "generate",
                "--name",
                "bar",
                "--profile",
                "small-cli",
                "--output",
                str(output),
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, result.stderr
        assert (output / ".gitignore").exists()
