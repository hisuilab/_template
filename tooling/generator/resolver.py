"""RESOLVE stage: topological sort of Part dependencies."""

from __future__ import annotations

from template.schema.part_schema import PartSchema
from tooling.generator.errors import ResolveError


def resolve(parts: list[PartSchema]) -> list[PartSchema]:
    """Return parts in topological dependency order (requires satisfied before dependants)."""
    by_id = {p.id: p for p in parts}

    for part in parts:
        for req in part.requires:
            if req not in by_id:
                raise ResolveError(
                    f"part '{part.id}' requires '{req}', which is not in the parts list"
                )

    for part in parts:
        for conflict_id in part.conflicts:
            if conflict_id in by_id:
                raise ResolveError(
                    f"part '{part.id}' conflicts with '{conflict_id}': both cannot be used together"
                )

    result: list[PartSchema] = []
    visited: set[str] = set()
    in_stack: set[str] = set()

    def visit(part_id: str) -> None:
        if part_id in in_stack:
            raise ResolveError(f"circular dependency detected involving '{part_id}'")
        if part_id in visited:
            return
        in_stack.add(part_id)
        for req in by_id[part_id].requires:
            visit(req)
        in_stack.discard(part_id)
        visited.add(part_id)
        result.append(by_id[part_id])

    for part in parts:
        visit(part.id)

    return result
