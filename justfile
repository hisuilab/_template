set shell := ["bash", "-euo", "pipefail", "-c"]

# requires: treefmt
format:
    treefmt

# requires: treefmt
check-format:
    treefmt --fail-on-change

# requires: rumdl
check-docs:
    if [ -d docs ]; then rumdl check --config rumdl.toml docs/; fi

# requires: git
check-readme:
    ./scripts/check-readme

# requires: git
check-status:
    ./scripts/check-status

# requires: git
check-encoding:
    ./scripts/check-encoding

# requires: bats
test-bats:
    bats --recursive tests/unit

# requires: pytest
test-py:
    pytest

# requires: bats, pytest
test: test-bats test-py

lint: check-format

verify: test lint check-docs check-readme check-status check-encoding

# =============================================================================
# Workspace — ~/Projects 初期化
# =============================================================================

# ~/Projects ワークスペースを初期化する（flake.nix / .envrc / justfile を配置）
init-workspace path="~/Projects" workspace="default":
    nix run .# -- init-workspace --path {{path}} --workspace {{workspace}}

# =============================================================================
# GitHub — repository setup and status
# =============================================================================

# requires: gh
# 全 GitHub 設定を適用する（.github/rules-preset に従い冪等）
github-setup:
    #!/usr/bin/env bash
    set -euo pipefail
    preset="$(cat .github/rules-preset 2>/dev/null || echo solo)"
    just github-setup-rules "$preset"

# requires: gh, jq
# Rules プリセットを適用または更新し .github/rules-preset を記録する（default: solo）
github-setup-rules $preset="solo":
    #!/usr/bin/env bash
    bash scripts/github-setup-rules "$preset"

# requires: gh, jq
# 全 GitHub 設定の現状を表示する
github-status:
    just github-rules-status

# requires: gh, jq
# 現在 GitHub に適用されている Rules を表示する
github-rules-status:
    #!/usr/bin/env bash
    set -euo pipefail
    if ! gh repo view --json nameWithOwner -q .nameWithOwner > /dev/null 2>&1; then
      echo "No GitHub remote configured."
      exit 0
    fi
    repo="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
    preset="$(cat .github/rules-preset 2>/dev/null || echo '(unknown)')"
    echo "=== Rules: ${repo} (preset: ${preset}) ==="
    gh api "repos/${repo}/rulesets" \
      --header "X-GitHub-Api-Version: 2022-11-28" \
      | jq '.[] | {id, name, enforcement, updated_at}'
