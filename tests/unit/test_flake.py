"""Tests for flake.nix outputs."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_flake_exposes_packages_output() -> None:
    content = (REPO_ROOT / "flake.nix").read_text()
    assert "packages = forAllSystems" in content


def test_flake_exposes_apps_output() -> None:
    content = (REPO_ROOT / "flake.nix").read_text()
    assert "apps" in content


def test_flake_app_wraps_generator() -> None:
    content = (REPO_ROOT / "flake.nix").read_text()
    assert "tooling.generator" in content


def test_flake_app_sets_template_root() -> None:
    content = (REPO_ROOT / "flake.nix").read_text()
    assert 'TEMPLATE_ROOT="${self}/template"' in content
