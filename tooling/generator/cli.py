"""CLI implementation for tooling.generator."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

from template.schema.profile_schema import ProfileSchema
from tooling.generator.applier import apply
from tooling.generator.errors import (
    ApplyError,
    LoadError,
    PlanError,
    RenderError,
    ResolveError,
    WorkspaceError,
)
from tooling.generator.loader import load_parts_for_profile, load_profile
from tooling.generator.models import GenerateRequest, LangSpec
from tooling.generator.planner import plan
from tooling.generator.renderer import render
from tooling.generator.resolver import resolve

_TEMPLATE_ROOT = Path(
    os.environ.get("TEMPLATE_ROOT", str(Path(__file__).resolve().parents[2] / "template"))
)


def _available_langs(template_root: Path) -> list[str]:
    lang_dir = template_root / "parts" / "lang"
    if not lang_dir.exists():
        return []
    return sorted(p.name for p in lang_dir.iterdir() if p.is_dir())


def _cmd_generate(args: argparse.Namespace) -> int:
    output = Path(args.output).expanduser().resolve()
    available = _available_langs(_TEMPLATE_ROOT)

    if args.lang is None:
        avail_str = ", ".join(available) if available else "(none)"
        print(f"error: --lang is required. Available: {avail_str}", file=sys.stderr)
        return 1
    lang_value: str = args.lang
    if "," in lang_value:
        print(
            "error: multiple --lang values not supported in M5 (planned for M6+)",
            file=sys.stderr,
        )
        return 1
    if "=" in lang_value:
        print(
            "error: role=lang syntax not supported in M5 (planned for M6+)",
            file=sys.stderr,
        )
        return 1
    if lang_value not in available:
        avail_str = ", ".join(available) if available else "(none)"
        print(
            f"error: unknown lang '{lang_value}'. Available: {avail_str}",
            file=sys.stderr,
        )
        return 1

    lang_spec = LangSpec(lang=lang_value, role=None)
    request = GenerateRequest(
        name=args.name,
        profile_id=args.profile,
        output_path=output,
        lang=(lang_spec,),
    )
    try:
        profile = load_profile(args.profile, _TEMPLATE_ROOT)
        extended_profile = ProfileSchema(
            name=profile.name,
            summary=profile.summary,
            parts=profile.parts + (f"lang/{lang_spec.lang}",),
            variables=profile.variables,
        )
        parts = load_parts_for_profile(extended_profile, _TEMPLATE_ROOT)
        parts = resolve(parts)
        gen_plan = plan(request, parts, template_root=_TEMPLATE_ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            staging = Path(tmp) / "staging"
            staging.mkdir()
            render(gen_plan, staging)
            result = apply(staging, output)
        print(f"Generated {len(result.files_written)} files in {result.output_path}")
        return 0
    except (LoadError, ResolveError, PlanError, RenderError, ApplyError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _cmd_init_workspace(args: argparse.Namespace) -> int:
    from tooling.generator.workspace import init_workspace

    path = Path(args.path).expanduser().resolve()
    workspace_root = _TEMPLATE_ROOT / "workspaces"

    try:
        init_workspace(
            path=path,
            workspace_name=args.workspace,
            workspace_root=workspace_root,
        )
        print(f"Initialized workspace at {path}")
        return 0
    except WorkspaceError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(prog="python3 -m tooling.generator")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Generate a new project from a profile")
    gen.add_argument("--name", required=True, help="Project name")
    gen.add_argument("--profile", required=True, help="Profile ID (e.g. small-cli)")
    gen.add_argument("--output", required=True, help="Output directory path")
    gen.add_argument("--lang", default=None, help="Language runtime (e.g. python, typescript)")

    iws = sub.add_parser("init-workspace", help="Initialize a ~/Projects workspace")
    iws.add_argument("--path", required=True, help="Target directory to initialize")
    iws.add_argument(
        "--workspace", default="default", help="Workspace template name (default: default)"
    )

    args = parser.parse_args()
    if args.command == "generate":
        sys.exit(_cmd_generate(args))
    elif args.command == "init-workspace":
        sys.exit(_cmd_init_workspace(args))
