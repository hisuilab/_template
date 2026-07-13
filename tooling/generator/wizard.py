"""WIZARD stage: interactive prompt sequence for project creation."""

from __future__ import annotations

import sys
from dataclasses import dataclass

import questionary


@dataclass
class WizardAnswers:
    name: str
    output: str
    lang: str
    profile: str


def _ask_or_exit(prompt) -> str:
    answer = prompt.ask()
    if answer is None:
        sys.exit(0)
    return answer


def run_wizard(available_langs: list[str], available_profiles: list[str]) -> WizardAnswers:
    name = _ask_or_exit(questionary.text("Project name:"))
    default_output = f"./{name}/{name}-main"
    raw_output = _ask_or_exit(questionary.text(f"Output path [{default_output}]:"))
    output = raw_output if raw_output else default_output
    lang = _ask_or_exit(questionary.select("Language:", choices=available_langs))
    profile = _ask_or_exit(questionary.select("Profile:", choices=available_profiles))
    return WizardAnswers(name=name, output=output, lang=lang, profile=profile)
