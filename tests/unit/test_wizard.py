"""Unit tests for tooling.generator.wizard."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from tooling.generator.wizard import WizardAnswers, run_wizard

_LANGS = ["python", "typescript"]
_PROFILES = ["small-cli", "small-library", "small-web-api"]


class TestRunWizardBasic:
    def test_run_wizard_returns_wizard_answers(self) -> None:
        text_mock = MagicMock()
        text_mock.ask.side_effect = ["my-app"]
        select_mock = MagicMock()
        select_mock.ask.side_effect = ["python", "small-cli"]

        with (
            patch("tooling.generator.wizard.questionary.text", return_value=text_mock),
            patch("tooling.generator.wizard.questionary.select", return_value=select_mock),
        ):
            result = run_wizard(_LANGS, _PROFILES)

        assert isinstance(result, WizardAnswers)
        assert result.name == "my-app"
        assert result.lang == "python"
        assert result.profile == "small-cli"

    def test_run_wizard_passes_choices_to_select(self) -> None:
        """run_wizard must forward available_langs / available_profiles to questionary.select."""
        text_mock = MagicMock()
        text_mock.ask.side_effect = ["app"]
        select_mock = MagicMock()
        select_mock.ask.side_effect = ["python", "small-cli"]

        with (
            patch("tooling.generator.wizard.questionary.text", return_value=text_mock),
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

    def test_wizard_answers_has_no_output_field(self) -> None:
        """WizardAnswers no longer contains an output path — output is computed by the caller."""
        answers = WizardAnswers(name="x", lang="python", profile="small-cli")
        assert not hasattr(answers, "output")


class TestRunWizardExitBehaviour:
    def test_run_wizard_exits_cleanly_when_name_is_none(self) -> None:
        """Ctrl+C on the first prompt returns None; run_wizard should exit cleanly."""
        text_mock = MagicMock()
        text_mock.ask.return_value = None

        with (
            patch("tooling.generator.wizard.questionary.text", return_value=text_mock),
            patch("tooling.generator.wizard.questionary.select"),
        ):
            with pytest.raises(SystemExit):
                run_wizard(_LANGS, _PROFILES)

    def test_run_wizard_exits_cleanly_when_lang_is_none(self) -> None:
        """Ctrl+C on the lang select returns None; run_wizard should exit cleanly."""
        text_mock = MagicMock()
        text_mock.ask.side_effect = ["my-app"]
        select_mock = MagicMock()
        select_mock.ask.return_value = None

        with (
            patch("tooling.generator.wizard.questionary.text", return_value=text_mock),
            patch("tooling.generator.wizard.questionary.select", return_value=select_mock),
        ):
            with pytest.raises(SystemExit):
                run_wizard(_LANGS, _PROFILES)


class TestRunWizardPrefill:
    def test_prefill_name_skips_name_question(self) -> None:
        """When name is prefilled, questionary.text must not be called."""
        select_mock = MagicMock()
        select_mock.ask.side_effect = ["python", "small-cli"]

        with (
            patch("tooling.generator.wizard.questionary.text") as mock_text,
            patch("tooling.generator.wizard.questionary.select", return_value=select_mock),
        ):
            result = run_wizard(_LANGS, _PROFILES, prefill={"name": "prefilled"})

        mock_text.assert_not_called()
        assert result.name == "prefilled"
        assert result.lang == "python"

    def test_prefill_lang_skips_lang_question(self) -> None:
        """When lang is prefilled, the lang select prompt must not be called."""
        text_mock = MagicMock()
        text_mock.ask.side_effect = ["myapp"]
        profile_select_mock = MagicMock()
        profile_select_mock.ask.return_value = "small-cli"

        with (
            patch("tooling.generator.wizard.questionary.text", return_value=text_mock),
            patch(
                "tooling.generator.wizard.questionary.select",
                return_value=profile_select_mock,
            ) as mock_select,
        ):
            result = run_wizard(_LANGS, _PROFILES, prefill={"lang": "typescript"})

        assert result.lang == "typescript"
        assert mock_select.call_count == 1
        _, kwargs = mock_select.call_args
        assert set(kwargs.get("choices", [])) == set(_PROFILES)

    def test_prefill_profile_skips_profile_question(self) -> None:
        """When profile is prefilled, the profile select prompt must not be called."""
        text_mock = MagicMock()
        text_mock.ask.side_effect = ["myapp"]
        lang_select_mock = MagicMock()
        lang_select_mock.ask.return_value = "python"

        with (
            patch("tooling.generator.wizard.questionary.text", return_value=text_mock),
            patch(
                "tooling.generator.wizard.questionary.select",
                return_value=lang_select_mock,
            ) as mock_select,
        ):
            result = run_wizard(_LANGS, _PROFILES, prefill={"profile": "small-library"})

        assert result.profile == "small-library"
        assert mock_select.call_count == 1
        _, kwargs = mock_select.call_args
        assert set(kwargs.get("choices", [])) == set(_LANGS)

    def test_prefill_all_skips_all_questions(self) -> None:
        """When all fields are prefilled, no interactive prompts are shown."""
        with (
            patch("tooling.generator.wizard.questionary.text") as mock_text,
            patch("tooling.generator.wizard.questionary.select") as mock_select,
        ):
            result = run_wizard(
                _LANGS,
                _PROFILES,
                prefill={"name": "myapp", "lang": "python", "profile": "small-cli"},
            )

        mock_text.assert_not_called()
        mock_select.assert_not_called()
        assert result.name == "myapp"
        assert result.lang == "python"
        assert result.profile == "small-cli"
