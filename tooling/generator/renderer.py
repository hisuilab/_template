"""RENDER stage: substitute {{var}} in content and write to staging directory."""

from __future__ import annotations

import re
import stat
from pathlib import Path

from tooling.generator.errors import RenderError
from tooling.generator.models import GenerationPlan

_PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")


def _render_file(src: Path, dest_path: str, variables: dict[str, str], staging: Path) -> None:
    out = staging / dest_path
    out.parent.mkdir(parents=True, exist_ok=True)

    try:
        content = src.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        out.write_bytes(src.read_bytes())
        out.chmod(stat.S_IMODE(src.stat().st_mode))
        return

    unresolved: list[str] = []

    def _replace(m: re.Match) -> str:
        var = m.group(1)
        if var in variables:
            return variables[var]
        unresolved.append(var)
        return m.group(0)

    rendered = _PLACEHOLDER_RE.sub(_replace, content)

    if unresolved:
        raise RenderError(f"unresolved placeholder(s) {unresolved!r} in '{dest_path}'")

    out.write_text(rendered, encoding="utf-8")
    out.chmod(stat.S_IMODE(src.stat().st_mode))


def _render_appended_files(
    pfiles: list, dest_path: str, variables: dict[str, str], staging: Path
) -> None:
    """Render multiple fragment files into one output by concatenating their rendered content.

    Fragments are separated by a single blank line to preserve readability.
    Each fragment is substituted independently so {{placeholders}} work in all fragments.
    """
    out = staging / dest_path
    out.parent.mkdir(parents=True, exist_ok=True)

    rendered_parts: list[str] = []
    unresolved: list[str] = []

    for pfile in pfiles:
        try:
            content = pfile.src_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raise RenderError(f"binary file cannot be used with append strategy: '{dest_path}'")

        def _replace(m: re.Match) -> str:
            var = m.group(1)
            if var in variables:
                return variables[var]
            unresolved.append(var)
            return m.group(0)

        rendered_parts.append(_PLACEHOLDER_RE.sub(_replace, content))

    if unresolved:
        raise RenderError(f"unresolved placeholder(s) {unresolved!r} in '{dest_path}'")

    # Join fragments with a single blank line between them.
    combined = "\n".join(part.rstrip("\n") for part in rendered_parts) + "\n"
    out.write_text(combined, encoding="utf-8")
    # Use permissions from the first fragment's source file.
    out.chmod(stat.S_IMODE(pfiles[0].src_path.stat().st_mode))


def render(plan: GenerationPlan, staging_dir: Path) -> None:
    # Group PlannedFiles by dest_path to detect append groups.
    groups: dict[str, list] = {}
    for pfile in plan.files:
        groups.setdefault(pfile.dest_path, []).append(pfile)

    for dest_path, pfiles in groups.items():
        if len(pfiles) == 1:
            _render_file(pfiles[0].src_path, dest_path, plan.variables, staging_dir)
        else:
            # Multiple fragments for the same dest_path — combine via append strategy.
            _render_appended_files(pfiles, dest_path, plan.variables, staging_dir)
