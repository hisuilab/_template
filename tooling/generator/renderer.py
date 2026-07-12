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


def render(plan: GenerationPlan, staging_dir: Path) -> None:
    for pfile in plan.files:
        _render_file(pfile.src_path, pfile.dest_path, plan.variables, staging_dir)
