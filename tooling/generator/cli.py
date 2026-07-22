"""CLI implementation for tooling.generator."""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path

from template.schema.profile_schema import ProfileSchema
from tooling.generator.applier import apply, inject
from tooling.generator.errors import (
    ApplyError,
    LoadError,
    ManifestError,
    PlanError,
    RenderError,
    ResolveError,
    WorkspaceError,
)
from tooling.generator.loader import load_part, load_parts_for_profile, load_profile
from tooling.generator.manifest import read_manifest, update_manifest, write_manifest
from tooling.generator.models import GenerateRequest, LangSpec, RoleSpec
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


def _available_profiles(template_root: Path) -> list[str]:
    profiles_dir = template_root / "profiles"
    if not profiles_dir.exists():
        return []
    return sorted(p.stem for p in profiles_dir.iterdir() if p.suffix == ".toml")


_NAME_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")


def _validate_name(name: str) -> str | None:
    """Return an error message if name is invalid, else None."""
    if not _NAME_RE.match(name):
        return (
            f"error: invalid project name '{name}'. "
            "Only alphanumerics, hyphens, and underscores are allowed."
        )
    return None


def _resolve_output_path(name: str, output_parent: str | None) -> Path:
    """Compute the final generation destination.

    --output absent  → {cwd}/{name}/{name}-main
    --output PARENT  → PARENT/{name}
    """
    if output_parent is not None:
        return Path(output_parent).expanduser().resolve() / name
    return Path.cwd() / name / f"{name}-main"


def _validate_lang(lang_value: str, available: list[str]) -> tuple[LangSpec | None, str | None]:
    """Return (LangSpec, None) on success or (None, error_message) on failure."""
    if "," in lang_value:
        return None, "error: multiple --lang values not supported in M5 (planned for M6+)"
    if "=" in lang_value:
        return None, "error: role=lang syntax not supported in M5 (planned for M6+)"
    if lang_value not in available:
        avail_str = ", ".join(available) if available else "(none)"
        return None, f"error: unknown lang '{lang_value}'. Available: {avail_str}"
    return LangSpec(lang=lang_value, role=None), None


def _validate_profile(profile: str, available: list[str]) -> str | None:
    """Return an error message if profile is invalid, else None."""
    if profile not in available:
        avail_str = ", ".join(available) if available else "(none)"
        return f"error: unknown profile '{profile}'. Available: {avail_str}"
    return None


def _starter_lang_parts(
    profile_parts: tuple[str, ...], lang: str, template_root: Path
) -> tuple[str, ...]:
    """Return companion '<starter-id>-<lang>' part ids that exist on disk."""
    candidates = []
    for part_id in profile_parts:
        if part_id.startswith("starter/"):
            candidate = f"{part_id}-{lang}"
            if (template_root / "parts" / candidate / "part.toml").exists():
                candidates.append(candidate)
    return tuple(candidates)


def _do_generate(name: str, profile: str, lang: str | None, output: Path) -> int:
    """Run the generation pipeline with a pre-resolved output path."""
    available = _available_langs(_TEMPLATE_ROOT)

    lang_spec: LangSpec | None = None
    if lang is not None:
        lang_spec, err = _validate_lang(lang, available)
        if err:
            print(err, file=sys.stderr)
            return 1

    request = GenerateRequest(
        name=name,
        profile_id=profile,
        output_path=output,
        lang=(lang_spec,) if lang_spec else (),
    )
    try:
        loaded_profile = load_profile(profile, _TEMPLATE_ROOT)
        extra_parts: tuple[str, ...] = ()
        if lang_spec:
            extra_parts = (f"lang/{lang_spec.lang}",) + _starter_lang_parts(
                loaded_profile.parts, lang_spec.lang, _TEMPLATE_ROOT
            )
        extended_profile = ProfileSchema(
            name=loaded_profile.name,
            summary=loaded_profile.summary,
            category=loaded_profile.category,
            parts=loaded_profile.parts + extra_parts,
            variables=loaded_profile.variables,
        )
        parts = load_parts_for_profile(extended_profile, _TEMPLATE_ROOT)
        parts = resolve(parts)
        gen_plan = plan(
            request,
            parts,
            template_root=_TEMPLATE_ROOT,
            profile_variables=extended_profile.variables,
        )
        with tempfile.TemporaryDirectory() as tmp:
            staging = Path(tmp) / "staging"
            staging.mkdir()
            render(gen_plan, staging)
            result = apply(staging, output)
        try:
            write_manifest(output, parts, project_name=name)
        except ManifestError as e:
            print(
                f"Warning: files were generated but manifest creation failed: {e}\n"
                f"To recover: delete '{output}' and re-run generate.",
                file=sys.stderr,
            )
            return 2
        print(f"Generated {len(result.files_written)} files in {result.output_path}")
        return 0
    except (
        LoadError,
        ResolveError,
        PlanError,
        RenderError,
        ApplyError,
        OSError,
    ) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _parse_role(role_str: str) -> tuple[str | None, str | None, str | None]:
    """Parse 'name:profile=<p>[,lang=<l>]' into (name, profile, lang)."""
    if ":" not in role_str:
        return None, None, None
    name, _, rest = role_str.partition(":")
    kv = dict(pair.split("=", 1) for pair in rest.split(",") if "=" in pair)
    return name, kv.get("profile"), kv.get("lang")


def _write_role_readme(output_root: Path, roles: list[RoleSpec]) -> None:
    lines = [f"# {output_root.name}", "", "## Roles", ""]
    for role in roles:
        lines.append(
            f"- `{role.name}/`: profile=`{role.profile}`, lang=`{role.lang or '(omitted)'}`"
        )
    lines += ["", "## Getting started", ""]
    for role in roles:
        lines += [
            "```sh",
            f"cd {role.name}",
            "nix develop --command just init",
            "nix develop",
            "just verify",
            "```",
            "",
        ]
    output_root.mkdir(parents=True, exist_ok=True)
    readme_path = output_root / "README.md"
    try:
        with readme_path.open("x") as f:
            f.write("\n".join(lines))
    except FileExistsError as e:
        raise ApplyError(f"output root README already exists: '{readme_path}'") from e


def _generate_roles(name: str, output_root: Path, roles: list[RoleSpec]) -> int:
    """Generate one independent sub-project per role under output_root."""
    readme_path = output_root / "README.md"
    if readme_path.exists():
        print(f"Error: output root README already exists: '{readme_path}'", file=sys.stderr)
        return 1

    print(f"→ Generating {len(roles)} role(s) at {output_root}...")
    failed: list[str] = []
    for role in roles:
        rc = _do_generate(name, role.profile, role.lang, output_root / role.name)
        if rc != 0:
            failed.append(role.name)

    if len(failed) == len(roles):
        return 1

    try:
        _write_role_readme(output_root, roles)
    except (ApplyError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if failed:
        failed_str = ", ".join(failed)
        print(
            f"Partial success: {len(roles) - len(failed)}/{len(roles)} role(s) generated.\n"
            f"Failed roles: {failed_str}\n"
            f"Re-run generate --role for each failed role to retry.",
            file=sys.stderr,
        )
        return 2
    print(f"Generated {len(roles)} role(s) in {output_root}")
    return 0


def _cmd_generate(args: argparse.Namespace) -> int:
    name_error = _validate_name(args.name)
    if name_error:
        print(name_error, file=sys.stderr)
        return 1

    if args.role and (args.profile or args.lang):
        print("error: --role cannot be combined with --profile/--lang", file=sys.stderr)
        return 1

    output = _resolve_output_path(args.name, args.output)

    if args.role:
        roles: list[RoleSpec] = []
        for role_str in args.role:
            role_name, profile, lang = _parse_role(role_str)
            if not role_name or not profile:
                print(
                    f"error: invalid --role format '{role_str}'. "
                    "Expected 'name:profile=<p>[,lang=<l>]'",
                    file=sys.stderr,
                )
                return 1
            role_name_error = _validate_name(role_name)
            if role_name_error:
                print(role_name_error, file=sys.stderr)
                return 1
            roles.append(RoleSpec(name=role_name, profile=profile, lang=lang))

        available_profiles = _available_profiles(_TEMPLATE_ROOT)
        available_langs = _available_langs(_TEMPLATE_ROOT)
        for role in roles:
            profile_error = _validate_profile(role.profile, available_profiles)
            if profile_error:
                print(profile_error, file=sys.stderr)
                return 1
            if role.lang is not None:
                _, lang_error = _validate_lang(role.lang, available_langs)
                if lang_error:
                    print(lang_error, file=sys.stderr)
                    return 1

        return _generate_roles(args.name, output, roles)

    if not args.profile:
        print("error: --profile is required unless --role is used", file=sys.stderr)
        return 1

    print(f"→ Generating at {output}...")
    return _do_generate(args.name, args.profile, args.lang, output)


def _cmd_create(args: argparse.Namespace) -> int:
    from tooling.generator.wizard import run_wizard

    available_langs = _available_langs(_TEMPLATE_ROOT)
    available_profiles = _available_profiles(_TEMPLATE_ROOT)

    prefill: dict[str, str] = {}
    if args.name is not None:
        prefill["name"] = args.name
    if args.lang is not None:
        prefill["lang"] = args.lang
    if args.profile is not None:
        prefill["profile"] = args.profile

    # Early-validate prefilled lang / profile before entering the wizard
    if "lang" in prefill:
        _, err = _validate_lang(prefill["lang"], available_langs)
        if err:
            print(err, file=sys.stderr)
            return 1
    if "profile" in prefill:
        err = _validate_profile(prefill["profile"], available_profiles)
        if err:
            print(err, file=sys.stderr)
            return 1

    # Warn if no choices are available (would cause silent exit in wizard)
    if not available_langs and "lang" not in prefill:
        print("error: no language parts found in template", file=sys.stderr)
        return 1
    if not available_profiles and "profile" not in prefill:
        print("error: no profiles found in template", file=sys.stderr)
        return 1

    profiles = [
        (profile_id, load_profile(profile_id, _TEMPLATE_ROOT).category)
        for profile_id in available_profiles
    ]
    answers = run_wizard(available_langs, profiles, prefill=prefill)

    name_error = _validate_name(answers.name)
    if name_error:
        print(name_error, file=sys.stderr)
        return 1

    output = _resolve_output_path(answers.name, args.output)

    if answers.roles:
        return _generate_roles(answers.name, output, answers.roles)

    print(f"→ Generating at {output}...")
    return _do_generate(answers.name, answers.profile, answers.lang, output)


_PART_ID_RE = re.compile(r"^[a-zA-Z0-9/_-]+$")


def _validate_part_id(part_id: str) -> str | None:
    """Return an error message if part_id is invalid, else None."""
    if not _PART_ID_RE.match(part_id) or ".." in part_id:
        return (
            f"error: invalid part id '{part_id}'. "
            "Only alphanumerics, forward slashes, hyphens, and underscores are allowed."
        )
    return None


def _cmd_inject(args: argparse.Namespace) -> int:
    target = Path(args.target).expanduser().resolve()
    part_id: str = args.part

    part_id_error = _validate_part_id(part_id)
    if part_id_error:
        print(part_id_error, file=sys.stderr)
        return 1

    try:
        manifest = read_manifest(target)
    except ManifestError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if part_id in manifest.applied_part_ids:
        print(
            f"Error: part '{part_id}' is already applied to this project.",
            file=sys.stderr,
        )
        return 1

    try:
        part = load_part(part_id, _TEMPLATE_ROOT)
    except LoadError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    missing = [r for r in part.requires if r not in manifest.applied_part_ids]
    if missing:
        for m in missing:
            print(
                f"Error: required part '{m}' has not been applied. Run: just inject {m}",
                file=sys.stderr,
            )
        return 1

    conflicting = [c for c in part.conflicts if c in manifest.applied_part_ids]
    if conflicting:
        for c in conflicting:
            print(
                f"Error: part '{part_id}' conflicts with already-applied part '{c}'.",
                file=sys.stderr,
            )
        return 1

    request = GenerateRequest(
        name=manifest.project_name,
        profile_id=part_id,
        output_path=target,
    )
    try:
        gen_plan = plan(request, [part], template_root=_TEMPLATE_ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            staging = Path(tmp) / "staging"
            staging.mkdir()
            render(gen_plan, staging)
            result = inject(staging, target)
        if not result.files_added:
            print(
                f"Injected '{part_id}': all {len(result.files_skipped)} file(s) already existed. "
                "No changes made; manifest not updated. Re-run inject to retry.",
                file=sys.stderr,
            )
            return 0
        try:
            update_manifest(target, part_id=part_id)
        except ManifestError as e:
            print(
                f"Warning: files were injected but manifest update failed: {e}\n"
                f"To recover, manually run: just inject {part_id}",
                file=sys.stderr,
            )
            return 2
        print(
            f"Injected '{part_id}': "
            f"{len(result.files_added)} added, {len(result.files_skipped)} skipped"
        )
        return 0
    except (PlanError, RenderError, ApplyError, OSError) as e:
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
            run_flake_update=not args.no_flake_update,
        )
        print(f"Initialized workspace at {path}")
        print()
        print("Next steps:")
        print(f"  cd {path}")
        print("  just new      # create your first project interactively")
        return 0
    except WorkspaceError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(prog="python3 -m tooling.generator")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Generate a new project from a profile")
    gen.add_argument("--name", required=True, help="Project name")
    gen.add_argument(
        "--profile",
        default=None,
        help="Profile ID (e.g. small-cli). Required unless --role is used",
    )
    gen.add_argument(
        "--output",
        default=None,
        help="Parent directory; generated at OUTPUT/name (default: current directory)",
    )
    gen.add_argument("--lang", default=None, help="Language runtime (e.g. python, typescript)")
    gen.add_argument(
        "--role",
        action="append",
        default=[],
        help=(
            "Monorepo-style sub-generation per role "
            "(e.g. backend:profile=starter-web-api,lang=python). Repeatable"
        ),
    )

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

    crt = sub.add_parser("create", help="Interactively create a new project (wizard)")
    crt.add_argument("name", nargs="?", default=None, help="Project name (skips name prompt)")
    crt.add_argument("--lang", default=None, help="Language runtime (skips lang prompt)")
    crt.add_argument("--profile", default=None, help="Profile ID (skips profile prompt)")
    crt.add_argument(
        "--output",
        default=None,
        help="Parent directory; generated at OUTPUT/name (default: current directory)",
    )

    inj = sub.add_parser("inject", help="Inject a Part into an existing generated project")
    inj.add_argument(
        "--part", required=True, help="Part ID to inject (e.g. features/logging-python)"
    )
    inj.add_argument("--target", required=True, help="Target project directory")

    args = parser.parse_args()
    if args.command == "generate":
        sys.exit(_cmd_generate(args))
    elif args.command == "inject":
        sys.exit(_cmd_inject(args))
    elif args.command == "init-workspace":
        sys.exit(_cmd_init_workspace(args))
    elif args.command == "create":
        sys.exit(_cmd_create(args))
