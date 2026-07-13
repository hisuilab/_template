"""Payload completeness tests for template/parts/.

Integration tests that verify each Part's payload/ directory is non-empty and
that placeholder variables ({{var}}) in file contents and paths are properly
declared in the Part's part.toml.

test_payload_is_not_empty is intentionally RED until the implement phase
creates the payload files.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

TEMPLATE_ROOT = Path(__file__).resolve().parents[2] / "template"
PARTS_ROOT = TEMPLATE_ROOT / "parts"
PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")


def _discover_parts() -> list[tuple[str, Path]]:
    parts = []
    for part_toml in sorted(PARTS_ROOT.rglob("part.toml")):
        part_dir = part_toml.parent
        with part_toml.open("rb") as f:
            data = tomllib.load(f)
        part_id = data["part"]["id"]
        parts.append((part_id, part_dir))
    return parts


def _payload_files(part_dir: Path) -> list[Path]:
    payload_dir = part_dir / "payload"
    if not payload_dir.is_dir():
        return []
    return [p for p in payload_dir.rglob("*") if p.is_file()]


def _declared_placeholders(part_dir: Path) -> set[str]:
    part_toml = part_dir / "part.toml"
    with part_toml.open("rb") as f:
        data = tomllib.load(f)
    return set(data.get("placeholders", {}).get("required", []))


PARTS = _discover_parts()


# ---------------------------------------------------------------------------
# Payload completeness (RED until implement phase)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("part_id,part_dir", PARTS, ids=[p[0] for p in PARTS])
def test_payload_is_not_empty(part_id: str, part_dir: Path) -> None:
    """Each Part must have at least one file in its payload/ directory."""
    files = _payload_files(part_dir)
    assert files, (
        f"payload/ is empty for part '{part_id}' ({part_dir}). Add template files under payload/."
    )


# ---------------------------------------------------------------------------
# Placeholder declaration consistency
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("part_id,part_dir", PARTS, ids=[p[0] for p in PARTS])
def test_no_undeclared_placeholders(part_id: str, part_dir: Path) -> None:
    """All {{var}} in payload file paths and contents must be in placeholders_required."""
    declared = _declared_placeholders(part_dir)
    payload_dir = part_dir / "payload"
    undeclared: dict[str, list[str]] = {}

    for path in _payload_files(part_dir):
        rel = str(path.relative_to(payload_dir))
        for var in PLACEHOLDER_RE.findall(rel):
            if var not in declared:
                undeclared.setdefault(rel, []).append(f"path:{var}")
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, IsADirectoryError):
            continue
        for var in PLACEHOLDER_RE.findall(content):
            if var not in declared:
                undeclared.setdefault(rel, []).append(f"content:{var}")

    assert not undeclared, (
        f"Undeclared placeholders in part '{part_id}':\n"
        + "\n".join(f"  {f}: {vs}" for f, vs in undeclared.items())
        + f"\nDeclared: {sorted(declared)}"
    )


# ---------------------------------------------------------------------------
# features/logging-* content checks
# ---------------------------------------------------------------------------


def test_logging_python_provides_get_logger() -> None:
    logger_py = PARTS_ROOT / "features" / "logging-python" / "payload" / "src" / "logger.py"
    assert logger_py.exists(), "src/logger.py not found in features/logging-python payload"
    content = logger_py.read_text(encoding="utf-8")
    assert "def get_logger" in content, "get_logger function missing from logger.py"
    assert "logging" in content, "stdlib logging import missing from logger.py"


def test_logging_typescript_provides_get_logger() -> None:
    logger_ts = PARTS_ROOT / "features" / "logging-typescript" / "payload" / "src" / "logger.ts"
    assert logger_ts.exists(), "src/logger.ts not found in features/logging-typescript payload"
    content = logger_ts.read_text(encoding="utf-8")
    assert "getLogger" in content, "getLogger function missing from logger.ts"


# ---------------------------------------------------------------------------
# features/ai-agent content checks
# ---------------------------------------------------------------------------


def test_ai_agent_provides_claude_dev_policy() -> None:
    dev_policy = (
        PARTS_ROOT / "features" / "ai-agent" / "payload" / "dot-claude" / "rules" / "dev-policy.md"
    )
    assert dev_policy.exists(), (
        "dot-claude/rules/dev-policy.md not found in features/ai-agent payload"
    )


# ---------------------------------------------------------------------------
# features/github-rulesets content checks
# ---------------------------------------------------------------------------


def test_github_rulesets_provides_solo_json() -> None:
    solo = (
        PARTS_ROOT
        / "features"
        / "github-rulesets"
        / "payload"
        / "dot-github"
        / "rulesets"
        / "solo.json"
    )
    assert solo.exists(), (
        "dot-github/rulesets/solo.json not found in features/github-rulesets payload"
    )


def test_github_rulesets_provides_team_json() -> None:
    team = (
        PARTS_ROOT
        / "features"
        / "github-rulesets"
        / "payload"
        / "dot-github"
        / "rulesets"
        / "team.json"
    )
    assert team.exists(), (
        "dot-github/rulesets/team.json not found in features/github-rulesets payload"
    )


def test_github_rulesets_provides_github_setup_rules() -> None:
    script = (
        PARTS_ROOT / "features" / "github-rulesets" / "payload" / "scripts" / "github-setup-rules"
    )
    assert script.exists(), (
        "scripts/github-setup-rules not found in features/github-rulesets payload"
    )
    assert script.stat().st_mode & 0o111, "scripts/github-setup-rules is not executable"


def test_github_rulesets_provides_rules_preset() -> None:
    preset = PARTS_ROOT / "features" / "github-rulesets" / "payload" / "dot-github" / "rules-preset"
    assert preset.exists(), "dot-github/rules-preset not found in features/github-rulesets payload"
    assert preset.read_text(encoding="utf-8").strip() == "solo", (
        "dot-github/rules-preset initial value must be 'solo'"
    )


def test_github_rulesets_json_are_valid() -> None:
    import json

    rulesets_dir = (
        PARTS_ROOT / "features" / "github-rulesets" / "payload" / "dot-github" / "rulesets"
    )
    for json_file in sorted(rulesets_dir.glob("*.json")):
        data = json.loads(json_file.read_text(encoding="utf-8"))
        assert data.get("name"), f"{json_file.name}: missing 'name' field"
        assert data.get("rules"), f"{json_file.name}: missing 'rules' field"
        assert data.get("enforcement") == "active", (
            f"{json_file.name}: enforcement must be 'active'"
        )
