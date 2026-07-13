"""Schema unit and integration tests for template/schema/.

Unit tests (fixtures): validate schema logic in isolation.
Integration tests (actual files): validate that the real part.toml and
profile.toml files in template/ satisfy the schema.  These tests are
intentionally RED until the implementation phase creates those files.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from template.schema.errors import SchemaError
from template.schema.part_schema import FileRule, PartSchema, validate_part
from template.schema.profile_schema import ProfileSchema, validate_profile

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "schema"
TEMPLATE_ROOT = Path(__file__).resolve().parents[2] / "template"


def _load_fixture(name: str) -> dict:
    with (FIXTURES / name).open("rb") as f:
        return tomllib.load(f)


def _load_toml(path: Path) -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)


# ---------------------------------------------------------------------------
# PartSchema — unit tests using fixtures
# ---------------------------------------------------------------------------


def test_valid_part_minimal_parses() -> None:
    schema = validate_part(_load_fixture("valid_part.toml"), source="valid_part.toml")
    assert schema == PartSchema(
        id="base",
        layer="base",
        summary="全 Profile 共通の開発基盤（Nix flake・just・pre-commit・CI）",
    )


def test_valid_part_full_parses() -> None:
    schema = validate_part(_load_fixture("valid_part_full.toml"), source="valid_part_full.toml")
    assert schema == PartSchema(
        id="features/ai-agent",
        layer="features",
        summary="AI エージェント向け設定ファイルを追加します",
        requires=("base",),
        conflicts=(),
        placeholders_required=("project_name",),
        files=(
            FileRule(path="AGENTS.md", strategy="error"),
            FileRule(path=".gitignore", strategy="replace"),
        ),
    )


def test_missing_id_is_rejected() -> None:
    with pytest.raises(SchemaError, match="part.id"):
        validate_part(
            _load_fixture("invalid_part_missing_id.toml"),
            source="invalid_part_missing_id.toml",
        )


def test_unknown_layer_is_rejected() -> None:
    with pytest.raises(SchemaError, match="part.layer"):
        validate_part(
            _load_fixture("invalid_part_bad_layer.toml"),
            source="invalid_part_bad_layer.toml",
        )


def test_unknown_strategy_is_rejected() -> None:
    with pytest.raises(SchemaError, match="strategy"):
        validate_part(
            _load_fixture("invalid_part_bad_strategy.toml"),
            source="invalid_part_bad_strategy.toml",
        )


def test_missing_part_table_is_rejected() -> None:
    with pytest.raises(SchemaError, match=r"\[part\]"):
        validate_part({}, source="<empty>")


# ---------------------------------------------------------------------------
# ProfileSchema — unit tests using fixtures
# ---------------------------------------------------------------------------


def test_valid_profile_parses() -> None:
    schema = validate_profile(_load_fixture("valid_profile.toml"), source="valid_profile.toml")
    assert schema == ProfileSchema(
        name="small-cli",
        summary="小規模 CLI ツール向けプロファイル",
        parts=("base", "scale/small", "purpose/cli"),
        variables={},
    )


def test_empty_parts_is_rejected() -> None:
    with pytest.raises(SchemaError, match="profile.parts"):
        validate_profile(
            _load_fixture("invalid_profile_empty_parts.toml"),
            source="invalid_profile_empty_parts.toml",
        )


def test_non_string_variable_is_rejected() -> None:
    with pytest.raises(SchemaError, match="variables"):
        validate_profile(
            _load_fixture("invalid_profile_bad_variable_type.toml"),
            source="invalid_profile_bad_variable_type.toml",
        )


def test_missing_profile_table_is_rejected() -> None:
    with pytest.raises(SchemaError, match=r"\[profile\]"):
        validate_profile({}, source="<empty>")


# ---------------------------------------------------------------------------
# Integration — actual template/ files (RED until implement phase)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "profile_name",
    ["small-cli", "small-web-api", "small-library"],
)
def test_profile_toml_validates(profile_name: str) -> None:
    path = TEMPLATE_ROOT / "profiles" / f"{profile_name}.toml"
    assert path.exists(), f"profile not found: {path}"
    schema = validate_profile(_load_toml(path), source=str(path))
    assert schema.name == profile_name
    assert len(schema.parts) >= 1


def test_all_part_tomls_validate() -> None:
    part_files = list((TEMPLATE_ROOT / "parts").rglob("part.toml"))
    assert len(part_files) >= 1, "no part.toml files found under template/parts/"
    for path in part_files:
        validate_part(_load_toml(path), source=str(path))
