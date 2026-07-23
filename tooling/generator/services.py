"""Selection and preflight services for the generator pipeline.

Responsibilities: validate lang/profile inputs and resolve the extended
ProfileSchema (with lang companion Parts) independently of the CLI layer.
Both the ``generate`` and ``create`` commands call these functions so that
preflight logic is guaranteed to be identical across both entry points.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from template.schema.profile_schema import ProfileSchema
from tooling.generator.errors import LoadError
from tooling.generator.loader import load_profile
from tooling.generator.models import LangSpec


@dataclass(frozen=True)
class SelectionResult:
    """Result of profile extension.

    Holds the lang-companion-Parts-extended ProfileSchema together with the
    resolved LangSpec (or None when no ``--lang`` was supplied).
    """

    extended_profile: ProfileSchema
    lang_spec: LangSpec | None


def validate_lang(lang_value: str, available: list[str]) -> tuple[LangSpec | None, str | None]:
    """Validate a lang value and return ``(LangSpec, None)`` or ``(None, error_msg)``."""
    if "," in lang_value:
        return None, "error: multiple --lang values not supported in M5 (planned for M6+)"
    if "=" in lang_value:
        return None, "error: role=lang syntax not supported in M5 (planned for M6+)"
    if lang_value not in available:
        avail_str = ", ".join(available) if available else "(none)"
        return None, f"error: unknown lang '{lang_value}'. Available: {avail_str}"
    return LangSpec(lang=lang_value, role=None), None


def validate_profile(profile: str, available: list[str]) -> str | None:
    """Validate a profile value and return an error message or ``None``."""
    if profile not in available:
        avail_str = ", ".join(available) if available else "(none)"
        return f"error: unknown profile '{profile}'. Available: {avail_str}"
    return None


def _available_langs_from_root(template_root: Path) -> list[str]:
    """Return sorted lang names from ``parts/lang/`` in *template_root*.

    Mirrors the ``_available_langs`` helper in ``cli.py`` without creating a
    services→cli dependency.
    """
    lang_dir = template_root / "parts" / "lang"
    if not lang_dir.exists():
        return []
    return sorted(p.name for p in lang_dir.iterdir() if p.is_dir())


def _starter_lang_parts(
    profile_parts: tuple[str, ...], lang: str, template_root: Path
) -> tuple[str, ...]:
    """Return companion ``<starter-id>-<lang>`` part ids that exist on disk."""
    candidates = []
    for part_id in profile_parts:
        if part_id.startswith("starter/"):
            candidate = f"{part_id}-{lang}"
            if (template_root / "parts" / candidate / "part.toml").exists():
                candidates.append(candidate)
    return tuple(candidates)


def resolve_selection(
    profile_id: str,
    lang: str | None,
    template_root: Path,
) -> SelectionResult:
    """Load a profile and extend it with lang companion Parts.

    Raises ``LoadError`` when the profile cannot be found; the caller is
    responsible for printing the error and returning a non-zero exit code.

    Both the ``generate`` and ``create`` commands must call this function so
    that the identical preflight and profile-extension logic is applied
    regardless of which entry point is used (fixes issue #132 P-4).
    """
    loaded_profile = load_profile(profile_id, template_root)

    lang_spec: LangSpec | None = None
    extra_parts: tuple[str, ...] = ()

    if lang is not None:
        available_langs = _available_langs_from_root(template_root)
        _lang_spec, err = validate_lang(lang, available_langs)
        if err:
            raise LoadError(err)
        lang_spec = LangSpec(lang=lang, role=None)
        extra_parts = (f"lang/{lang}",) + _starter_lang_parts(
            loaded_profile.parts, lang, template_root
        )

    extended_profile = ProfileSchema(
        name=loaded_profile.name,
        summary=loaded_profile.summary,
        category=loaded_profile.category,
        parts=loaded_profile.parts + extra_parts,
        variables=loaded_profile.variables,
    )
    return SelectionResult(extended_profile=extended_profile, lang_spec=lang_spec)
