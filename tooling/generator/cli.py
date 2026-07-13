"""CLI implementation for tooling.generator."""

from __future__ import annotations

import argparse
import os
import re
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


_NAME_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")


def _validate_name(name: str) -> str | None:
    """Return an error message if name is invalid, else None."""
    if not _NAME_RE.match(name):
        return (
            f"error: invalid project name '{name}'. "
            "Only alphanumerics, hyphens, and underscores are allowed."
        )
    return None


def _cmd_generate(args: argparse.Namespace) -> int:
    name_error = _validate_name(args.name)
    if name_error:
        print(name_error, file=sys.stderr)
        return 1

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


def _cmd_create(_args: argparse.Namespace) -> int:
    from tooling.generator.wizard import run_wizard

    available_langs = _available_langs(_TEMPLATE_ROOT)
    profiles_dir = _TEMPLATE_ROOT / "profiles"
    available_profiles = (
        sorted(p.stem for p in profiles_dir.iterdir() if p.suffix == ".toml")
        if profiles_dir.exists()
        else []
    )

    answers = run_wizard(available_langs, available_profiles)
    output = Path(answers.output).expanduser().resolve()
    print(f"→ Generating at {output}...")
    return _cmd_generate(
        argparse.Namespace(
            name=answers.name,
            profile=answers.profile,
            lang=answers.lang,
            output=str(output),
        )
    )


def _cmd_init_workspace(args: argparse.Namespace) -> int:
    from tooling.generator.workspace import init_workspace

    path = Path(args.path).expanduser().resolve()
    workspace_root = _TEMPLATE_ROOT / "workspaces"

    try:
        init_workspace(
            path=path,
            workspace_name=args.workspace,
            workspace_root=workspace_root,
            run_flake_update=not args.no_flake_update,
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
    iws.add_argument(
        "--no-flake-update",
        action="store_true",
        default=False,
        help="Skip 'nix flake update' after initialization (useful in tests or offline environments)",
    )

    sub.add_parser("create", help="Interactively create a new project (wizard)")

    args = parser.parse_args()
    if args.command == "generate":
        sys.exit(_cmd_generate(args))
    elif args.command == "init-workspace":
        sys.exit(_cmd_init_workspace(args))
    elif args.command == "create":
        sys.exit(_cmd_create(args))
