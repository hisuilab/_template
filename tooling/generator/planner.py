"""PLAN stage: variable binding, file name transformation, collision detection."""

from __future__ import annotations

import re
from pathlib import Path

from template.schema.part_schema import PartSchema
from tooling.generator.errors import PlanError
from tooling.generator.models import GenerateRequest, GenerationPlan, PlannedFile

_PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")
_DOT_PREFIX = "dot-"


def _substitute(text: str, variables: dict[str, str]) -> str:
    return _PLACEHOLDER_RE.sub(lambda m: variables.get(m.group(1), m.group(0)), text)


def _strip_dot_prefix(name: str) -> str:
    if name.startswith(_DOT_PREFIX):
        return "." + name[len(_DOT_PREFIX) :]
    return name


def _transform_path(rel: str, variables: dict[str, str]) -> str:
    parts = rel.replace("\\", "/").split("/")
    return "/".join(_strip_dot_prefix(_substitute(p, variables)) for p in parts)


def _file_strategy(part: PartSchema, dest_path: str) -> str:
    # rule.path is in the dest_path space (after dot- stripping and placeholder substitution)
    for rule in part.files:
        if rule.path == dest_path:
            return rule.strategy
    return "error"


def plan(
    request: GenerateRequest,
    parts: list[PartSchema],
    template_root: Path,
) -> GenerationPlan:
    variables: dict[str, str] = {"project_name": request.name}

    for part in parts:
        for ph in part.placeholders_required:
            if ph not in variables:
                ph_repr = "{{" + ph + "}}"
                raise PlanError(
                    f"part '{part.id}' requires placeholder '{ph_repr}' "
                    f"but it was not provided (available: {sorted(variables.keys())})"
                )

    planned: dict[str, PlannedFile] = {}

    for part in parts:
        payload_dir = template_root / "parts" / part.id / "payload"
        for src in sorted(payload_dir.rglob("*")):
            if not src.is_file():
                continue
            rel = str(src.relative_to(payload_dir))
            dest = _transform_path(rel, variables)
            strategy = _file_strategy(part, dest)

            if dest in planned:
                if strategy == "replace":
                    planned[dest] = PlannedFile(src_path=src, dest_path=dest, strategy=strategy)
                else:
                    raise PlanError(
                        f"file '{dest}' is provided by multiple parts "
                        f"(use strategy='replace' to allow overwriting)"
                    )
            else:
                planned[dest] = PlannedFile(src_path=src, dest_path=dest, strategy=strategy)

    return GenerationPlan(request=request, variables=variables, files=tuple(planned.values()))
