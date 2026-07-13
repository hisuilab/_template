"""WIZARD stage: interactive prompt sequence for project creation."""

from __future__ import annotations

import sys
from dataclasses import dataclass

import questionary


@dataclass
class WizardAnswers:
    name: str
    lang: str
    profile: str


def _ask_or_exit(prompt) -> str:
    answer = prompt.ask()
    if answer is None:
        sys.exit(0)
    return answer


def run_wizard(
    available_langs: list[str],
    available_profiles: list[str],
    prefill: dict[str, str] | None = None,
) -> WizardAnswers:
    p = prefill or {}

    if "name" in p:
        name = p["name"]
    else:
        name = _ask_or_exit(questionary.text("Project name:"))

    if "lang" in p:
        lang = p["lang"]
    else:
        lang = _ask_or_exit(questionary.select("Language:", choices=available_langs))

    if "profile" in p:
        profile = p["profile"]
    else:
        profile = _ask_or_exit(questionary.select("Profile:", choices=available_profiles))

    return WizardAnswers(name=name, lang=lang, profile=profile)
