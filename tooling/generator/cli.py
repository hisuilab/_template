"""CLI implementation for tooling.generator."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from tooling.generator.applier import apply
from tooling.generator.errors import ApplyError, LoadError, PlanError, RenderError, ResolveError
from tooling.generator.loader import load_parts_for_profile, load_profile
from tooling.generator.models import GenerateRequest
from tooling.generator.planner import plan
from tooling.generator.renderer import render
from tooling.generator.resolver import resolve

_TEMPLATE_ROOT = Path(__file__).resolve().parents[2] / "template"


def _cmd_generate(args: argparse.Namespace) -> int:
    output = Path(args.output).expanduser().resolve()
    request = GenerateRequest(name=args.name, profile_id=args.profile, output_path=output)
    try:
        profile = load_profile(args.profile, _TEMPLATE_ROOT)
        parts = load_parts_for_profile(profile, _TEMPLATE_ROOT)
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


def main() -> None:
    parser = argparse.ArgumentParser(prog="python3 -m tooling.generator")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Generate a new project from a profile")
    gen.add_argument("--name", required=True, help="Project name")
    gen.add_argument("--profile", required=True, help="Profile ID (e.g. small-cli)")
    gen.add_argument("--output", required=True, help="Output directory path")

    args = parser.parse_args()
    if args.command == "generate":
        sys.exit(_cmd_generate(args))
