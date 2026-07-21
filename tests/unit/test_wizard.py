"""Unit tests for tooling.generator.wizard."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tooling.generator.models import RoleSpec
from tooling.generator.wizard import WizardAnswers, run_wizard

_LANGS = ["python", "typescript"]
_PROFILES = [
    ("starter-cli", "cli"),
    ("starter-library", "library"),
    ("starter-web-api", "web"),
    ("starter-web-htmx", "web"),
]


def _mock_prompts(text_answers: list[str], select_answers: list[str]):
    text_mock = MagicMock()
    text_mock.ask.side_effect = text_answers
    select_mock = MagicMock()
    select_mock.ask.side_effect = select_answers
    return text_mock, select_mock


class TestRunWizardCliIntent:
    def test_cli_intent_auto_selects_sole_profile(self) -> None:
        """Only one 'cli' category profile exists, so it must not be asked."""
        text_mock, select_mock = _mock_prompts(["my-app"], ["CLI tool", "python"])

        with (
            patch("tooling.generator.wizard.questionary.text", return_value=text_mock),
            patch("tooling.generator.wizard.questionary.select", return_value=select_mock),
        ):
            result = run_wizard(_LANGS, _PROFILES)

        assert result == WizardAnswers(
            name="my-app", profile="starter-cli", lang="python", roles=[]
        )

    def test_intent_choices_are_forwarded_to_select(self) -> None:
        text_mock, select_mock = _mock_prompts(["my-app"], ["CLI tool", "python"])

        with (
            patch("tooling.generator.wizard.questionary.text", return_value=text_mock),
            patch(
                "tooling.generator.wizard.questionary.select", return_value=select_mock
            ) as mock_select,
        ):
            run_wizard(_LANGS, _PROFILES)

        first_call_kwargs = mock_select.call_args_list[0].kwargs
        assert set(first_call_kwargs.get("choices", [])) == {
            "CLI tool",
            "Web app",
            "Library",
            "Scaffold only (decide later)",
        }


class TestRunWizardLibraryIntent:
    def test_library_intent_auto_selects_sole_profile(self) -> None:
        text_mock, select_mock = _mock_prompts(["my-lib"], ["Library", "typescript"])

        with (
            patch("tooling.generator.wizard.questionary.text", return_value=text_mock),
            patch("tooling.generator.wizard.questionary.select", return_value=select_mock),
        ):
            result = run_wizard(_LANGS, _PROFILES)

        assert result == WizardAnswers(
            name="my-lib", profile="starter-library", lang="typescript", roles=[]
        )


class TestRunWizardWebMonolithIntent:
    def test_web_monolith_asks_profile_and_lang(self) -> None:
        text_mock, select_mock = _mock_prompts(
            ["my-web"],
            ["Web app", "No (single project)", "starter-web-api", "python"],
        )

        with (
            patch("tooling.generator.wizard.questionary.text", return_value=text_mock),
            patch("tooling.generator.wizard.questionary.select", return_value=select_mock),
        ):
            result = run_wizard(_LANGS, _PROFILES)

        assert result == WizardAnswers(
            name="my-web", profile="starter-web-api", lang="python", roles=[]
        )


class TestRunWizardWebSeparateIntent:
    def test_web_separate_builds_backend_and_frontend_roles(self) -> None:
        text_mock, select_mock = _mock_prompts(
            ["fullstack"],
            [
                "Web app",
                "Yes (separate backend/frontend)",
                "starter-web-api",
                "python",
                "starter-web-htmx",
                "typescript",
            ],
        )

        with (
            patch("tooling.generator.wizard.questionary.text", return_value=text_mock),
            patch("tooling.generator.wizard.questionary.select", return_value=select_mock),
        ):
            result = run_wizard(_LANGS, _PROFILES)

        assert result == WizardAnswers(
            name="fullstack",
            profile=None,
            lang=None,
            roles=[
                RoleSpec(name="backend", profile="starter-web-api", lang="python"),
                RoleSpec(name="frontend", profile="starter-web-htmx", lang="typescript"),
            ],
        )

    def test_web_separate_asks_lang_per_role_even_with_a_lang_prefill(self) -> None:
        """A single --lang prefill cannot represent two roles; each role must still be asked."""
        text_mock, select_mock = _mock_prompts(
            ["fullstack"],
            [
                "Web app",
                "Yes (separate backend/frontend)",
                "starter-web-api",
                "python",
                "starter-web-htmx",
                "typescript",
            ],
        )

        with (
            patch("tooling.generator.wizard.questionary.text", return_value=text_mock),
            patch("tooling.generator.wizard.questionary.select", return_value=select_mock),
        ):
            result = run_wizard(_LANGS, _PROFILES, prefill={"lang": "rust"})

        assert result.roles == [
            RoleSpec(name="backend", profile="starter-web-api", lang="python"),
            RoleSpec(name="frontend", profile="starter-web-htmx", lang="typescript"),
        ]


class TestRunWizardScaffoldOnlyIntent:
    def test_scaffold_only_skips_lang_and_asks_across_all_categories(self) -> None:
        text_mock, select_mock = _mock_prompts(
            ["placeholder"], ["Scaffold only (decide later)", "starter-cli"]
        )

        with (
            patch("tooling.generator.wizard.questionary.text", return_value=text_mock),
            patch(
                "tooling.generator.wizard.questionary.select", return_value=select_mock
            ) as mock_select,
        ):
            result = run_wizard(_LANGS, _PROFILES)

        assert result == WizardAnswers(
            name="placeholder", profile="starter-cli", lang=None, roles=[]
        )
        profile_call_kwargs = mock_select.call_args_list[1].kwargs
        assert set(profile_call_kwargs.get("choices", [])) == {
            "starter-cli",
            "starter-library",
            "starter-web-api",
            "starter-web-htmx",
        }

    def test_scaffold_only_still_honours_an_explicit_lang_prefill(self) -> None:
        """A user-supplied --lang must not be silently dropped by the scaffold-only branch."""
        text_mock, select_mock = _mock_prompts(
            ["placeholder"], ["Scaffold only (decide later)", "starter-cli"]
        )

        with (
            patch("tooling.generator.wizard.questionary.text", return_value=text_mock),
            patch("tooling.generator.wizard.questionary.select", return_value=select_mock),
        ):
            result = run_wizard(_LANGS, _PROFILES, prefill={"lang": "python"})

        assert result == WizardAnswers(
            name="placeholder", profile="starter-cli", lang="python", roles=[]
        )


class TestRunWizardExitBehaviour:
    def test_run_wizard_exits_cleanly_when_name_is_none(self) -> None:
        text_mock = MagicMock()
        text_mock.ask.return_value = None

        with (
            patch("tooling.generator.wizard.questionary.text", return_value=text_mock),
            patch("tooling.generator.wizard.questionary.select"),
        ):
            with pytest.raises(SystemExit):
                run_wizard(_LANGS, _PROFILES)

    def test_run_wizard_exits_cleanly_when_intent_is_none(self) -> None:
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
    def test_prefill_profile_skips_intent_question_but_still_asks_lang(self) -> None:
        text_mock, select_mock = _mock_prompts(["myapp"], ["python"])

        with (
            patch("tooling.generator.wizard.questionary.text", return_value=text_mock),
            patch(
                "tooling.generator.wizard.questionary.select", return_value=select_mock
            ) as mock_select,
        ):
            result = run_wizard(_LANGS, _PROFILES, prefill={"profile": "starter-web-api"})

        assert result == WizardAnswers(
            name="myapp", profile="starter-web-api", lang="python", roles=[]
        )
        assert mock_select.call_count == 1

    def test_prefill_profile_and_lang_skips_all_selects(self) -> None:
        with (
            patch("tooling.generator.wizard.questionary.text") as mock_text,
            patch("tooling.generator.wizard.questionary.select") as mock_select,
        ):
            result = run_wizard(
                _LANGS,
                _PROFILES,
                prefill={"name": "myapp", "lang": "python", "profile": "starter-cli"},
            )

        mock_text.assert_not_called()
        mock_select.assert_not_called()
        assert result == WizardAnswers(name="myapp", profile="starter-cli", lang="python", roles=[])

    def test_prefill_name_skips_name_question(self) -> None:
        select_mock = MagicMock()
        select_mock.ask.side_effect = ["CLI tool", "python"]

        with (
            patch("tooling.generator.wizard.questionary.text") as mock_text,
            patch("tooling.generator.wizard.questionary.select", return_value=select_mock),
        ):
            result = run_wizard(_LANGS, _PROFILES, prefill={"name": "prefilled"})

        mock_text.assert_not_called()
        assert result.name == "prefilled"
        assert result.profile == "starter-cli"
        assert result.lang == "python"


def test_wizard_answers_has_no_output_field() -> None:
    """WizardAnswers no longer contains an output path — output is computed by the caller."""
    answers = WizardAnswers(name="x", profile="starter-cli", lang="python")
    assert not hasattr(answers, "output")
    assert answers.roles == []
