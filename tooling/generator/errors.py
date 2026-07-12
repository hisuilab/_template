"""Error types for each generator pipeline stage."""

from __future__ import annotations


class LoadError(Exception):
    pass


class ResolveError(Exception):
    pass


class PlanError(Exception):
    pass


class RenderError(Exception):
    pass


class ApplyError(Exception):
    pass
