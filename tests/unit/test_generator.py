"""Unit and integration tests for tooling/generator/ pipeline.

All imports below are intentionally RED until the implementation phase
creates the tooling/generator/ modules.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

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
from tooling.generator.manifest import read_manifest, update_manifest, write_manifest
from tooling.generator.models import (
    GenerateRequest,
    GenerationPlan,
    GenerationResult,
    InjectResult,
    LangSpec,
    ManifestData,
    ManifestEntry,
    PlannedFile,
)
from tooling.generator.planner import plan as make_plan
from tooling.generator.renderer import render
from tooling.generator.resolver import resolve
from template.schema.part_schema import PartSchema
from template.schema.profile_schema import ProfileSchema

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
            category="cli",
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

    def test_plan_profile_variables_substituted_in_path(self, tmp_path: Path) -> None:
        self._make_part_dir(tmp_path, "base", {"src/{{app_name}}/main.py": ""})
        part = PartSchema(
            id="base",
            layer="base",
            summary="base",
            placeholders_required=("app_name",),
        )
        req = GenerateRequest(name="myproj", profile_id="test", output_path=tmp_path / "out")
        result = make_plan(
            req, [part], template_root=tmp_path, profile_variables={"app_name": "myapp"}
        )
        dest_paths = [f.dest_path for f in result.files]
        assert "src/myapp/main.py" in dest_paths

    def test_plan_profile_variables_cannot_override_project_name(self, tmp_path: Path) -> None:
        self._make_part_dir(tmp_path, "base", {"{{project_name}}/README.md": ""})
        part = PartSchema(
            id="base",
            layer="base",
            summary="base",
            placeholders_required=("project_name",),
        )
        req = GenerateRequest(name="myproj", profile_id="test", output_path=tmp_path / "out")
        result = make_plan(
            req,
            [part],
            template_root=tmp_path,
            profile_variables={"project_name": "evil"},
        )
        dest_paths = [f.dest_path for f in result.files]
        assert "myproj/README.md" in dest_paths
        assert "evil/README.md" not in dest_paths

    def test_plan_append_strategy_collects_both_parts(self, tmp_path: Path) -> None:
        """append strategy must include PlannedFiles from both base and lang parts (issue #134)."""
        from template.schema.part_schema import FileRule

        self._make_part_dir(tmp_path, "base", {"dot-gitignore": "# base\n.DS_Store\n"})
        self._make_part_dir(tmp_path, "lang/python", {"dot-gitignore": "# python\n__pycache__/\n"})
        base_part = PartSchema(id="base", layer="base", summary="base")
        lang_part = PartSchema(
            id="lang/python",
            layer="lang",
            summary="python",
            files=(FileRule(path=".gitignore", strategy="append"),),
        )
        req = GenerateRequest(name="x", profile_id="test", output_path=tmp_path / "out")
        result = make_plan(req, [base_part, lang_part], template_root=tmp_path)
        gitignore_files = [f for f in result.files if f.dest_path == ".gitignore"]
        assert len(gitignore_files) == 2, (
            f"Expected 2 PlannedFiles for .gitignore (base + lang), got {len(gitignore_files)}"
        )

    def test_plan_append_strategy_base_only_when_no_lang(self, tmp_path: Path) -> None:
        """When only base is present (--lang omitted), only one PlannedFile is collected (issue #134)."""
        self._make_part_dir(tmp_path, "base", {"dot-gitignore": "# base\n.DS_Store\n"})
        base_part = PartSchema(id="base", layer="base", summary="base")
        req = GenerateRequest(name="x", profile_id="test", output_path=tmp_path / "out")
        result = make_plan(req, [base_part], template_root=tmp_path)
        gitignore_files = [f for f in result.files if f.dest_path == ".gitignore"]
        assert len(gitignore_files) == 1

    def test_plan_part_variables_injected_into_context(self, tmp_path: Path) -> None:
        """Part variables must be merged into the plan context so templates can use them (issue #135)."""
        self._make_part_dir(tmp_path, "base", {"flake.nix": "packages = [{{lang_packages}}]\n"})
        base_part = PartSchema(
            id="base",
            layer="base",
            summary="base",
            variables={"lang_packages": ""},
        )
        req = GenerateRequest(name="x", profile_id="test", output_path=tmp_path / "out")
        result = make_plan(req, [base_part], template_root=tmp_path)
        assert "lang_packages" in result.variables

    def test_plan_lang_part_variables_override_base_defaults(self, tmp_path: Path) -> None:
        """Lang part's variables must override base part's default variables (issue #135)."""
        self._make_part_dir(tmp_path, "base", {"flake.nix": "packages = [{{lang_packages}}]\n"})
        self._make_part_dir(tmp_path, "lang/python", {"treefmt.nix": "# python\n"})
        base_part = PartSchema(
            id="base",
            layer="base",
            summary="base",
            variables={"lang_packages": ""},
        )
        lang_part = PartSchema(
            id="lang/python",
            layer="lang",
            summary="python",
            requires=("base",),
            variables={"lang_packages": "pkgs.python3\n              pkgs.ruff"},
        )
        req = GenerateRequest(name="x", profile_id="test", output_path=tmp_path / "out")
        result = make_plan(req, [base_part, lang_part], template_root=tmp_path)
        assert result.variables["lang_packages"] == "pkgs.python3\n              pkgs.ruff"

    def test_plan_part_variables_cannot_override_reserved_keys(self, tmp_path: Path) -> None:
        """Part variables must NOT override reserved keys like project_name (issue #135)."""
        self._make_part_dir(tmp_path, "base", {"README.md": "# {{project_name}}\n"})
        base_part = PartSchema(
            id="base",
            layer="base",
            summary="base",
            variables={"project_name": "evil-override"},
        )
        req = GenerateRequest(name="myproj", profile_id="test", output_path=tmp_path / "out")
        result = make_plan(req, [base_part], template_root=tmp_path)
        assert result.variables["project_name"] == "myproj"

    def test_plan_profile_variables_override_part_variables(self, tmp_path: Path) -> None:
        """Profile variables must override part variables (issue #135)."""
        self._make_part_dir(tmp_path, "base", {"flake.nix": "packages = [{{lang_packages}}]\n"})
        base_part = PartSchema(
            id="base",
            layer="base",
            summary="base",
            variables={"lang_packages": "pkgs.default"},
        )
        req = GenerateRequest(name="x", profile_id="test", output_path=tmp_path / "out")
        result = make_plan(
            req,
            [base_part],
            template_root=tmp_path,
            profile_variables={"lang_packages": "pkgs.overridden"},
        )
        assert result.variables["lang_packages"] == "pkgs.overridden"

    def test_plan_part_variables_render_into_file_content(self, tmp_path: Path) -> None:
        """Part variables injected into context must be substituted in file content (issue #135)."""
        payload = tmp_path / "parts" / "base" / "payload"
        payload.mkdir(parents=True)
        (payload / "flake.nix").write_text("packages = [\n{{lang_packages}}\n]\n")
        base_part = PartSchema(
            id="base",
            layer="base",
            summary="base",
            variables={"lang_packages": "pkgs.gh"},
        )
        req = GenerateRequest(name="x", profile_id="test", output_path=tmp_path / "out")
        gen_plan = make_plan(req, [base_part], template_root=tmp_path)
        staging = tmp_path / "staging"
        staging.mkdir()
        render(gen_plan, staging)
        content = (staging / "flake.nix").read_text()
        assert "pkgs.gh" in content
        assert "{{lang_packages}}" not in content

    def test_plan_profile_variables_reach_render_stage(self, tmp_path: Path) -> None:
        payload = tmp_path / "parts" / "base" / "payload"
        payload.mkdir(parents=True)
        (payload / "config.txt").write_text("app={{app_name}}\n")
        part = PartSchema(
            id="base",
            layer="base",
            summary="base",
            placeholders_required=("app_name",),
        )
        req = GenerateRequest(name="myproj", profile_id="test", output_path=tmp_path / "out")
        gen_plan = make_plan(
            req, [part], template_root=tmp_path, profile_variables={"app_name": "myapp"}
        )
        staging = tmp_path / "staging"
        staging.mkdir()
        render(gen_plan, staging)
        assert (staging / "config.txt").read_text() == "app=myapp\n"


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

    def test_render_append_strategy_combines_two_fragments(self, tmp_path: Path) -> None:
        """render() with two PlannedFiles for the same dest_path must concatenate them (issue #134)."""
        base_src = tmp_path / "base.txt"
        base_src.write_text("# base\n.DS_Store\n")
        lang_src = tmp_path / "lang.txt"
        lang_src.write_text("# python\n__pycache__/\n")
        staging = tmp_path / "staging"
        staging.mkdir()
        pfile_base = PlannedFile(src_path=base_src, dest_path=".gitignore", strategy="error")
        pfile_lang = PlannedFile(src_path=lang_src, dest_path=".gitignore", strategy="append")
        gen_plan = GenerationPlan(
            request=GenerateRequest(name="p", profile_id="t", output_path=tmp_path / "out"),
            variables={},
            files=(pfile_base, pfile_lang),
        )
        render(gen_plan, staging)
        content = (staging / ".gitignore").read_text()
        assert "# base" in content
        assert ".DS_Store" in content
        assert "# python" in content
        assert "__pycache__/" in content

    def test_render_append_strategy_no_duplicate_lines(self, tmp_path: Path) -> None:
        """render() combining base and lang fragments must not produce duplicate lines (issue #134)."""
        base_src = tmp_path / "base.txt"
        base_src.write_text("# base\n.DS_Store\n")
        lang_src = tmp_path / "lang.txt"
        lang_src.write_text("# python\n__pycache__/\n")
        staging = tmp_path / "staging"
        staging.mkdir()
        pfile_base = PlannedFile(src_path=base_src, dest_path=".gitignore", strategy="error")
        pfile_lang = PlannedFile(src_path=lang_src, dest_path=".gitignore", strategy="append")
        gen_plan = GenerationPlan(
            request=GenerateRequest(name="p", profile_id="t", output_path=tmp_path / "out"),
            variables={},
            files=(pfile_base, pfile_lang),
        )
        render(gen_plan, staging)
        content = (staging / ".gitignore").read_text()
        lines = [ln for ln in content.splitlines() if ln.strip()]
        assert len(lines) == len(set(lines)), f"duplicate lines found:\n{content}"

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

    def test_inject_rolls_back_added_files_on_io_error(self, tmp_path: Path) -> None:
        staging = tmp_path / "staging"
        staging.mkdir()
        (staging / "a.txt").write_text("a\n")
        (staging / "b.txt").write_text("b\n")
        output = tmp_path / "output"
        output.mkdir()

        call_count = 0

        original_copy2 = __import__("shutil").copy2

        def failing_copy2(src: object, dst: object) -> None:
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                raise OSError("simulated disk full")
            original_copy2(src, dst)

        with patch("tooling.generator.applier.shutil.copy2", side_effect=failing_copy2):
            with pytest.raises(ApplyError, match="I/O error"):
                inject(staging, output)

        remaining = list(output.iterdir())
        assert remaining == [], f"rollback failed: {remaining} still in output"


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

    def test_load_part_id_dir_mismatch_raises_load_error(self, tmp_path: Path) -> None:
        parts_dir = tmp_path / "parts" / "actual-dir"
        parts_dir.mkdir(parents=True)
        payload_dir = parts_dir / "payload"
        payload_dir.mkdir()
        (payload_dir / "README.md").write_text("# hello")
        (parts_dir / "part.toml").write_text(
            '[part]\nid = "different-id"\nlayer = "base"\nsummary = "mismatch"\n'
        )
        with pytest.raises(LoadError, match="different-id"):
            load_part("actual-dir", tmp_path)


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
            '[manifest]\nschema_version = "2"\nproject_name = "x"\ngenerated_at = "2026-01-01"\n'
            'template_revision = ""\ngenerator_version = ""\n\n'
            '[[applied]]\napplied_at = "2026-01-01"\n'
        )
        with pytest.raises(ManifestError, match="malformed"):
            read_manifest(tmp_path)

    def test_update_manifest_rejects_unsafe_part_id(self, tmp_path: Path) -> None:
        parts = [PartSchema(id="base", layer="base", summary="base")]
        write_manifest(tmp_path, parts, project_name="proj")
        with pytest.raises(ManifestError):
            update_manifest(tmp_path, part_id='evil"injection')


# ---------------------------------------------------------------------------
# Manifest v2 — RED tests (will pass after implementation)
# ---------------------------------------------------------------------------


class TestManifestV2:
    """Tests for manifest v2 schema: atomic write, new fields, validation."""

    # 1. atomic write — write_manifest uses tmp→rename
    def test_write_manifest_is_atomic(self, tmp_path: Path) -> None:
        """write_manifest() must write via .tmp then rename (no partial manifest left on error)."""
        from tooling.generator.manifest import MANIFEST_FILENAME

        parts = [PartSchema(id="base", layer="base", summary="base")]
        write_manifest(
            tmp_path,
            parts,
            project_name="myapp",
            files_by_part={"base": ["README.md", "flake.nix"]},
            template_revision="abc1234",
            generator_version="0.1.0",
        )
        # .tmp file must NOT remain after a successful write
        assert not (tmp_path / (MANIFEST_FILENAME + ".tmp")).exists()
        assert (tmp_path / MANIFEST_FILENAME).exists()

    # 2a. v2 schema — template_revision and generator_version in [manifest]
    def test_write_manifest_v2_header_fields(self, tmp_path: Path) -> None:
        parts = [PartSchema(id="base", layer="base", summary="base")]
        write_manifest(
            tmp_path,
            parts,
            project_name="myapp",
            files_by_part={"base": []},
            template_revision="abc1234",
            generator_version="0.1.0",
        )
        manifest = read_manifest(tmp_path)
        assert manifest.template_revision == "abc1234"
        assert manifest.generator_version == "0.1.0"

    # 2b. v2 schema — part_digest and files in [[applied]] entries
    def test_write_manifest_v2_entry_fields(self, tmp_path: Path) -> None:
        parts = [
            PartSchema(id="base", layer="base", summary="base"),
            PartSchema(id="starter/cli", layer="starter", summary="cli"),
        ]
        write_manifest(
            tmp_path,
            parts,
            project_name="myapp",
            files_by_part={
                "base": ["README.md", "flake.nix"],
                "starter/cli": ["justfile"],
            },
            template_revision="abc1234",
            generator_version="0.1.0",
        )
        manifest = read_manifest(tmp_path)
        assert len(manifest.applied_entries) == 2
        base_entry = next(e for e in manifest.applied_entries if e.part_id == "base")
        assert "README.md" in base_entry.files
        assert "flake.nix" in base_entry.files
        cli_entry = next(e for e in manifest.applied_entries if e.part_id == "starter/cli")
        assert "justfile" in cli_entry.files

    # 2c. v2 schema — part_digest field round-trips
    def test_write_manifest_v2_part_digest(self, tmp_path: Path) -> None:
        parts = [PartSchema(id="base", layer="base", summary="base")]
        write_manifest(
            tmp_path,
            parts,
            project_name="myapp",
            files_by_part={"base": []},
            template_revision="",
            generator_version="",
            part_digests={"base": "sha256:deadbeef"},
        )
        manifest = read_manifest(tmp_path)
        base_entry = next(e for e in manifest.applied_entries if e.part_id == "base")
        assert base_entry.part_digest == "sha256:deadbeef"

    # 3. v1 reading raises ManifestError
    def test_read_manifest_v1_raises_manifest_error(self, tmp_path: Path) -> None:
        from tooling.generator.manifest import MANIFEST_FILENAME

        (tmp_path / MANIFEST_FILENAME).write_text(
            '[manifest]\nschema_version = "1"\nproject_name = "old"\ngenerated_at = "2026-01-01"\n'
        )
        with pytest.raises(ManifestError, match="schema_version"):
            read_manifest(tmp_path)

    # 4a. broken TOML raises ManifestError
    def test_read_manifest_broken_toml_raises(self, tmp_path: Path) -> None:
        from tooling.generator.manifest import MANIFEST_FILENAME

        (tmp_path / MANIFEST_FILENAME).write_text("not valid toml ][")
        with pytest.raises(ManifestError, match="corrupt"):
            read_manifest(tmp_path)

    # 4b. duplicate part IDs raise ManifestError
    def test_read_manifest_duplicate_part_id_raises(self, tmp_path: Path) -> None:
        from tooling.generator.manifest import MANIFEST_FILENAME

        content = (
            '[manifest]\nschema_version = "2"\nproject_name = "x"\n'
            'generated_at = "2026-01-01"\ntemplate_revision = ""\ngenerator_version = ""\n\n'
            '[[applied]]\npart_id = "base"\napplied_at = "2026-01-01"\npart_digest = ""\nfiles = []\n\n'
            '[[applied]]\npart_id = "base"\napplied_at = "2026-01-01"\npart_digest = ""\nfiles = []\n'
        )
        (tmp_path / MANIFEST_FILENAME).write_text(content)
        with pytest.raises(ManifestError, match="duplicate"):
            read_manifest(tmp_path)

    # 4c. wrong type for files raises ManifestError
    def test_read_manifest_wrong_type_files_raises(self, tmp_path: Path) -> None:
        from tooling.generator.manifest import MANIFEST_FILENAME

        content = (
            '[manifest]\nschema_version = "2"\nproject_name = "x"\n'
            'generated_at = "2026-01-01"\ntemplate_revision = ""\ngenerator_version = ""\n\n'
            '[[applied]]\npart_id = "base"\napplied_at = "2026-01-01"\npart_digest = ""\nfiles = "not-a-list"\n'
        )
        (tmp_path / MANIFEST_FILENAME).write_text(content)
        with pytest.raises(ManifestError, match="files"):
            read_manifest(tmp_path)

    # update_manifest: atomic write (no append), preserves existing entries
    def test_update_manifest_is_atomic(self, tmp_path: Path) -> None:
        from tooling.generator.manifest import MANIFEST_FILENAME

        parts = [PartSchema(id="base", layer="base", summary="base")]
        write_manifest(
            tmp_path,
            parts,
            project_name="proj",
            files_by_part={"base": ["README.md"]},
            template_revision="",
            generator_version="",
        )
        update_manifest(
            tmp_path,
            part_id="features/logging-python",
            files=["src/logging.py"],
            part_digest="sha256:cafe",
        )
        # .tmp file must NOT remain after a successful update
        assert not (tmp_path / (MANIFEST_FILENAME + ".tmp")).exists()
        manifest = read_manifest(tmp_path)
        assert "base" in manifest.applied_part_ids
        assert "features/logging-python" in manifest.applied_part_ids

    # update_manifest: files and part_digest are written to the new entry
    def test_update_manifest_records_files_and_digest(self, tmp_path: Path) -> None:
        parts = [PartSchema(id="base", layer="base", summary="base")]
        write_manifest(
            tmp_path,
            parts,
            project_name="proj",
            files_by_part={"base": []},
            template_revision="",
            generator_version="",
        )
        update_manifest(
            tmp_path,
            part_id="features/logging-python",
            files=["src/logging.py"],
            part_digest="sha256:cafe",
        )
        manifest = read_manifest(tmp_path)
        entry = next(e for e in manifest.applied_entries if e.part_id == "features/logging-python")
        assert "src/logging.py" in entry.files
        assert entry.part_digest == "sha256:cafe"

    # ManifestEntry is importable from models
    def test_manifest_entry_is_dataclass(self) -> None:
        entry = ManifestEntry(part_id="base", applied_at="2026-01-01")
        assert entry.part_id == "base"
        assert entry.files == ()
        assert entry.part_digest == ""


class TestApplierManifestV2:
    """Tests that applier passes files_written/files_added to manifest correctly via cli."""

    def test_do_generate_passes_files_to_manifest(self, tmp_path: Path) -> None:
        """After generate, the manifest entry for each part must have a non-empty files list."""
        import tempfile

        from tooling.generator.applier import apply
        from tooling.generator.manifest import write_manifest

        # Write a manifest with files_by_part populated
        fake_part = PartSchema(id="base", layer="base", summary="base")
        write_manifest(
            tmp_path,
            [fake_part],
            project_name="proj",
            files_by_part={"base": ["README.md", "flake.nix"]},
            template_revision="abc",
            generator_version="0.1.0",
        )
        manifest = read_manifest(tmp_path)
        base_entry = next(e for e in manifest.applied_entries if e.part_id == "base")
        assert len(base_entry.files) > 0

    def test_cmd_inject_records_files_in_manifest(self, tmp_path: Path) -> None:
        """update_manifest with files= kwarg stores file list in the manifest entry."""
        parts = [PartSchema(id="base", layer="base", summary="base")]
        write_manifest(
            tmp_path,
            parts,
            project_name="proj",
            files_by_part={"base": []},
            template_revision="",
            generator_version="",
        )
        update_manifest(
            tmp_path,
            part_id="starter/cli",
            files=["justfile", "src/main.py"],
            part_digest="",
        )
        manifest = read_manifest(tmp_path)
        entry = next(e for e in manifest.applied_entries if e.part_id == "starter/cli")
        assert "justfile" in entry.files
        assert "src/main.py" in entry.files

    def test_cmd_inject_records_template_revision_in_manifest(self, tmp_path: Path) -> None:
        """write_manifest records template_revision; update_manifest preserves it."""
        parts = [PartSchema(id="base", layer="base", summary="base")]
        write_manifest(
            tmp_path,
            parts,
            project_name="proj",
            files_by_part={"base": []},
            template_revision="rev123",
            generator_version="0.1.0",
        )
        update_manifest(
            tmp_path,
            part_id="features/x",
            files=[],
            part_digest="",
        )
        manifest = read_manifest(tmp_path)
        assert manifest.template_revision == "rev123"


# ---------------------------------------------------------------------------
# Integration — full pipeline with real template files
# ---------------------------------------------------------------------------


class TestGeneratorIntegration:
    def test_generate_small_cli_creates_expected_files(self, tmp_path: Path) -> None:
        output = tmp_path / "foo"
        profile = load_profile("starter-cli", TEMPLATE_ROOT)
        # Mirror cli.py's --lang python injection: lang/python plus the
        # matching starter/cli-python composite Part provide src/main.py.
        profile = ProfileSchema(
            name=profile.name,
            summary=profile.summary,
            category=profile.category,
            parts=profile.parts + ("lang/python", "starter/cli-python"),
            variables=profile.variables,
        )
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

    def test_create_wizard_roles_generates_role_subdirectories(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When the wizard returns roles, _cmd_create must delegate to _generate_roles."""
        import argparse

        from tooling.generator import cli
        from tooling.generator.models import RoleSpec
        from tooling.generator.wizard import WizardAnswers

        monkeypatch.chdir(tmp_path)
        fake_answers = WizardAnswers(
            name="fullstack",
            profile=None,
            lang=None,
            roles=[
                RoleSpec(name="backend", profile="starter-web-api", lang="python"),
                RoleSpec(name="frontend", profile="starter-web-htmx", lang="typescript"),
            ],
        )
        args = argparse.Namespace(name=None, lang=None, profile=None, output=None)

        with patch("tooling.generator.wizard.run_wizard", return_value=fake_answers):
            rc = cli._cmd_create(args)

        assert rc == 0
        output = tmp_path / "fullstack" / "fullstack-main"
        assert (output / "backend" / "src" / "app.py").exists()
        assert (output / "frontend" / "templates" / "README.md").exists()


# ---------------------------------------------------------------------------
# Services — validate_lang, validate_profile, resolve_selection (issue #132)
# ---------------------------------------------------------------------------


class TestServicesValidateLang:
    """Unit tests for services.validate_lang.

    These tests are RED until tooling/generator/services.py is created.
    """

    def test_valid_lang_returns_lang_spec(self) -> None:
        from tooling.generator.services import validate_lang

        lang_spec, err = validate_lang("python", ["python", "typescript"])
        assert err is None
        assert lang_spec is not None
        assert lang_spec.lang == "python"
        assert lang_spec.role is None

    def test_unknown_lang_returns_error_message(self) -> None:
        from tooling.generator.services import validate_lang

        lang_spec, err = validate_lang("cobol", ["python", "typescript"])
        assert lang_spec is None
        assert err is not None
        assert "cobol" in err

    def test_unknown_lang_error_lists_available(self) -> None:
        from tooling.generator.services import validate_lang

        _, err = validate_lang("cobol", ["python", "typescript"])
        assert err is not None
        assert "python" in err or "typescript" in err

    def test_multiple_lang_via_comma_returns_error(self) -> None:
        from tooling.generator.services import validate_lang

        lang_spec, err = validate_lang("python,typescript", ["python", "typescript"])
        assert lang_spec is None
        assert err is not None

    def test_role_lang_syntax_returns_error(self) -> None:
        from tooling.generator.services import validate_lang

        lang_spec, err = validate_lang("backend=python", ["python"])
        assert lang_spec is None
        assert err is not None

    def test_empty_available_returns_error_with_none_hint(self) -> None:
        from tooling.generator.services import validate_lang

        _, err = validate_lang("python", [])
        assert err is not None
        # must not raise; should mention none or empty
        assert err != ""


class TestServicesValidateProfile:
    """Unit tests for services.validate_profile.

    These tests are RED until tooling/generator/services.py is created.
    """

    def test_valid_profile_returns_none(self) -> None:
        from tooling.generator.services import validate_profile

        err = validate_profile("starter-cli", ["starter-cli", "starter-web-api"])
        assert err is None

    def test_unknown_profile_returns_error_message(self) -> None:
        from tooling.generator.services import validate_profile

        err = validate_profile("no-such-profile", ["starter-cli"])
        assert err is not None
        assert "no-such-profile" in err

    def test_unknown_profile_error_lists_available(self) -> None:
        from tooling.generator.services import validate_profile

        err = validate_profile("ghost", ["starter-cli", "starter-web-api"])
        assert err is not None
        assert "starter-cli" in err or "starter-web-api" in err

    def test_empty_available_returns_error(self) -> None:
        from tooling.generator.services import validate_profile

        err = validate_profile("starter-cli", [])
        assert err is not None


class TestServicesResolveSelection:
    """Unit tests for services.resolve_selection.

    These tests are RED until tooling/generator/services.py is created.
    """

    def test_resolve_selection_without_lang_returns_base_profile(self) -> None:
        from tooling.generator.services import resolve_selection

        result = resolve_selection("starter-cli", lang=None, template_root=TEMPLATE_ROOT)
        assert result.lang_spec is None
        assert result.extended_profile is not None
        assert "base" in result.extended_profile.parts

    def test_resolve_selection_with_lang_includes_lang_part(self) -> None:
        from tooling.generator.services import resolve_selection

        result = resolve_selection("starter-cli", lang="python", template_root=TEMPLATE_ROOT)
        assert result.lang_spec is not None
        assert result.lang_spec.lang == "python"
        assert "lang/python" in result.extended_profile.parts

    def test_resolve_selection_with_lang_includes_companion_starter_part(self) -> None:
        from tooling.generator.services import resolve_selection

        result = resolve_selection("starter-cli", lang="python", template_root=TEMPLATE_ROOT)
        # starter/cli-python is the companion part for starter/cli + python
        assert "starter/cli-python" in result.extended_profile.parts

    def test_resolve_selection_with_nonexistent_companion_omits_it(self, tmp_path: Path) -> None:
        """If no starter/<id>-<lang> part exists on disk, it must not be included."""
        from tooling.generator.services import resolve_selection

        # tmp_path has no parts, so no companion can be found;
        # but we need a minimal profile to load, so build a small fixture.
        profiles_dir = tmp_path / "profiles"
        profiles_dir.mkdir()
        (profiles_dir / "mini.toml").write_text(
            '[profile]\nname = "mini"\nsummary = "minimal"\ncategory = "cli"\nparts = ["base"]\n'
        )
        parts_dir = tmp_path / "parts" / "base"
        parts_dir.mkdir(parents=True)
        (parts_dir / "part.toml").write_text(
            '[part]\nid = "base"\nlayer = "base"\nsummary = "base"\n'
        )
        (parts_dir / "payload").mkdir()

        result = resolve_selection("mini", lang="python", template_root=tmp_path)
        # lang/python part is added but no starter/base-python companion exists
        assert "lang/python" in result.extended_profile.parts
        # no companion whose starter id matches "base"
        assert not any(p.startswith("starter/") for p in result.extended_profile.parts)

    def test_resolve_selection_unknown_profile_raises_load_error(self) -> None:
        from tooling.generator.errors import LoadError
        from tooling.generator.services import resolve_selection

        with pytest.raises(LoadError):
            resolve_selection("no-such-profile", lang=None, template_root=TEMPLATE_ROOT)

    def test_resolve_selection_generate_and_create_share_same_expansion(self) -> None:
        """generate and create paths must produce identical extended_profile via resolve_selection.

        This guards the P-4 problem: both commands must run through the same preflight.
        """
        from tooling.generator.services import resolve_selection

        result_gen = resolve_selection("starter-cli", lang="python", template_root=TEMPLATE_ROOT)
        result_crt = resolve_selection("starter-cli", lang="python", template_root=TEMPLATE_ROOT)
        assert result_gen.extended_profile.parts == result_crt.extended_profile.parts
        assert result_gen.lang_spec == result_crt.lang_spec
