"""WIZARD stage: interactive prompt sequence for project creation."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

import questionary

from tooling.generator.models import RoleSpec

_INTENT_CHOICES = (
    ("CLI tool", "cli"),
    ("Web app", "web"),
    ("Library", "library"),
    ("Scaffold only (decide later)", None),
)

_ROLE_NAMES = ("backend", "frontend")

_SEPARATE_NO = "No (single project)"
_SEPARATE_YES = "Yes (separate backend/frontend)"


@dataclass
class WizardAnswers:
    name: str
    profile: str | None = None
    lang: str | None = None
    roles: list[RoleSpec] = field(default_factory=list)


def _ask_or_exit(prompt) -> str:
    answer = prompt.ask()
    if answer is None:
        sys.exit(0)
    return answer


def _ask_lang(available_langs: list[str], prefill_lang: str | None) -> str:
    if prefill_lang is not None:
        return prefill_lang
    return _ask_or_exit(questionary.select("Language:", choices=available_langs))


def _ask_profile(profile_ids: list[str]) -> str:
    if len(profile_ids) == 1:
        return profile_ids[0]
    return _ask_or_exit(questionary.select("Profile:", choices=profile_ids))


def _profiles_in_category(profiles: list[tuple[str, str]], category: str) -> list[str]:
    return [profile_id for profile_id, cat in profiles if cat == category]


def run_wizard(
    available_langs: list[str],
    profiles: list[tuple[str, str]],
    prefill: dict[str, str] | None = None,
) -> WizardAnswers:
    p = prefill or {}

    name = p["name"] if "name" in p else _ask_or_exit(questionary.text("Project name:"))

    if "profile" in p:
        lang = _ask_lang(available_langs, p.get("lang"))
        return WizardAnswers(name=name, profile=p["profile"], lang=lang, roles=[])

    intent_label = _ask_or_exit(
        questionary.select(
            "What do you want to build?",
            choices=[label for label, _ in _INTENT_CHOICES],
        )
    )
    category = dict(_INTENT_CHOICES)[intent_label]

    if category in ("cli", "library"):
        profile = _ask_profile(_profiles_in_category(profiles, category))
        lang = _ask_lang(available_langs, p.get("lang"))
        return WizardAnswers(name=name, profile=profile, lang=lang, roles=[])

    if category is None:
        profile = _ask_profile([profile_id for profile_id, _ in profiles])
        return WizardAnswers(name=name, profile=profile, lang=p.get("lang"), roles=[])

    web_profile_ids = _profiles_in_category(profiles, "web")
    separate_label = _ask_or_exit(
        questionary.select(
            "Separate frontend and backend?",
            choices=[_SEPARATE_NO, _SEPARATE_YES],
        )
    )
    if separate_label == _SEPARATE_NO:
        profile = _ask_profile(web_profile_ids)
        lang = _ask_lang(available_langs, p.get("lang"))
        return WizardAnswers(name=name, profile=profile, lang=lang, roles=[])

    # A single scalar --lang prefill can't represent two independently-chosen
    # roles, so each role is always asked regardless of prefill.
    roles = [
        RoleSpec(
            name=role_name,
            profile=_ask_profile(web_profile_ids),
            lang=_ask_lang(available_langs, None),
        )
        for role_name in _ROLE_NAMES
    ]
    return WizardAnswers(name=name, profile=None, lang=None, roles=roles)
