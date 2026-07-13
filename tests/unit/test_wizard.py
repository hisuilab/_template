"""Unit tests for tooling.generator.wizard."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from tooling.generator.wizard import WizardAnswers, run_wizard

_LANGS = ["python", "typescript"]
_PROFILES = ["small-cli", "small-library", "small-web-api"]


def _mock_ask(name: str, output: str, lang: str, profile: str) -> MagicMock:
    """Return a side_effect list for questionary.text / questionary.select .ask() calls."""
    text_mock = MagicMock()
    text_mock.ask.side_effect = [name, output]
    select_mock = MagicMock()
    select_mock.ask.side_effect = [lang, profile]
    return text_mock, select_mock


def test_run_wizard_returns_wizard_answers() -> None:
    text_answers = iter(["my-app", "./my-app/my-app-main"])
    select_answers = iter(["python", "small-cli"])

    text_mock = MagicMock()
    text_mock.ask.side_effect = lambda: next(text_answers)
    select_mock = MagicMock()
    select_mock.ask.side_effect = lambda: next(select_answers)

    with (
        patch("tooling.generator.wizard.questionary.text", return_value=text_mock),
        patch("tooling.generator.wizard.questionary.select", return_value=select_mock),
    ):
        result = run_wizard(_LANGS, _PROFILES)

    assert isinstance(result, WizardAnswers)
    assert result.name == "my-app"
    assert result.output == "./my-app/my-app-main"
    assert result.lang == "python"
    assert result.profile == "small-cli"


def test_run_wizard_default_output_uses_name() -> None:
    """When user accepts the default output path, it is name/name-main."""
    text_answers = iter(["proj", ""])
    select_answers = iter(["typescript", "small-library"])

    text_mock = MagicMock()
    text_mock.ask.side_effect = lambda: next(text_answers)
    select_mock = MagicMock()
    select_mock.ask.side_effect = lambda: next(select_answers)

    with (
        patch("tooling.generator.wizard.questionary.text", return_value=text_mock),
        patch("tooling.generator.wizard.questionary.select", return_value=select_mock),
    ):
        result = run_wizard(_LANGS, _PROFILES)

    assert result.output == "./proj/proj-main"


def test_run_wizard_passes_choices_to_select() -> None:
    """run_wizard must forward available_langs / available_profiles to questionary.select."""
    text_mock = MagicMock()
    text_mock.ask.side_effect = ["app", "./app/app-main"]
    select_mock = MagicMock()
    select_mock.ask.side_effect = ["python", "small-cli"]

    with (
        patch("tooling.generator.wizard.questionary.text", return_value=text_mock) as _,
        patch(
            "tooling.generator.wizard.questionary.select", return_value=select_mock
        ) as mock_select,
    ):
        run_wizard(_LANGS, _PROFILES)

    calls = mock_select.call_args_list
    assert len(calls) == 2
    _, first_kwargs = calls[0]
    _, second_kwargs = calls[1]
    assert set(first_kwargs.get("choices", [])) == set(_LANGS)
    assert set(second_kwargs.get("choices", [])) == set(_PROFILES)


def test_run_wizard_exits_cleanly_when_name_is_none() -> None:
    """Ctrl+C on the first prompt returns None; run_wizard should exit cleanly."""
    text_mock = MagicMock()
    text_mock.ask.return_value = None

    with (
        patch("tooling.generator.wizard.questionary.text", return_value=text_mock),
        patch("tooling.generator.wizard.questionary.select"),
    ):
        with pytest.raises(SystemExit):
            run_wizard(_LANGS, _PROFILES)


def test_run_wizard_exits_cleanly_when_lang_is_none() -> None:
    """Ctrl+C on the lang select returns None; run_wizard should exit cleanly."""
    text_answers = iter(["my-app", "./my-app/my-app-main"])
    text_mock = MagicMock()
    text_mock.ask.side_effect = lambda: next(text_answers)
    select_mock = MagicMock()
    select_mock.ask.return_value = None

    with (
        patch("tooling.generator.wizard.questionary.text", return_value=text_mock),
        patch("tooling.generator.wizard.questionary.select", return_value=select_mock),
    ):
        with pytest.raises(SystemExit):
            run_wizard(_LANGS, _PROFILES)
