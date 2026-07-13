"""WIZARD stage: interactive prompt sequence for project creation."""

from __future__ import annotations

from dataclasses import dataclass

import questionary


@dataclass
class WizardAnswers:
    name: str
    output: str
    lang: str
    profile: str


def run_wizard(available_langs: list[str], available_profiles: list[str]) -> WizardAnswers:
    name = questionary.text("Project name:").ask()
    default_output = f"./{name}/{name}-main"
    raw_output = questionary.text(f"Output path [{default_output}]:").ask()
    output = raw_output if raw_output else default_output
    lang = questionary.select("Language:", choices=available_langs).ask()
    profile = questionary.select("Profile:", choices=available_profiles).ask()
    return WizardAnswers(name=name, output=output, lang=lang, profile=profile)
