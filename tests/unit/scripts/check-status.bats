#!/usr/bin/env bats

setup() {
  repo_root="$(cd "$BATS_TEST_DIRNAME/../../.." && pwd)"
  test_dir="$(mktemp -d)"
  mkdir -p "$test_dir/scripts"
  ln -s "$repo_root/scripts/check-status" "$test_dir/scripts/check-status"
  cd "$test_dir" || return 1
  git init -q
  git config user.email test@example.com
  git config user.name test
}

teardown() {
  rm -rf "$test_dir"
}

@test "valid status in docs/draft passes" {
  mkdir -p docs/draft
  cat >docs/draft/example.md <<'EOF'
---
status: draft
---
# title
EOF
  git add docs

  run ./scripts/check-status

  [ "$status" -eq 0 ]
}

@test "missing frontmatter fails" {
  mkdir -p docs/draft
  cat >docs/draft/example.md <<'EOF'
# title

no frontmatter here
EOF
  git add docs

  run ./scripts/check-status

  [ "$status" -eq 1 ]
  [[ $output == *"missing frontmatter: docs/draft/example.md"* ]]
}

@test "missing status field fails" {
  mkdir -p docs/draft
  cat >docs/draft/example.md <<'EOF'
---
migrated_at: null
---
# title
EOF
  git add docs

  run ./scripts/check-status

  [ "$status" -eq 1 ]
  [[ $output == *"missing status field: docs/draft/example.md"* ]]
}

@test "invalid status value fails" {
  mkdir -p docs/draft
  cat >docs/draft/example.md <<'EOF'
---
status: aproved
---
# title
EOF
  git add docs

  run ./scripts/check-status

  [ "$status" -eq 1 ]
  [[ $output == *'invalid status "aproved" in docs/draft/example.md'* ]]
}

@test "README.md is exempt from status checks" {
  mkdir -p docs/draft
  cat >docs/draft/README.md <<'EOF'
# docs/draft

## 1. 概要

説明
EOF
  git add docs

  run ./scripts/check-status

  [ "$status" -eq 0 ]
}

@test "milestone and decision directories accept their own enum values" {
  mkdir -p docs/milestones docs/decisions
  cat >docs/milestones/m0-example.md <<'EOF'
---
status: in_progress
---
# M0
EOF
  cat >docs/decisions/2026-01-01-example.md <<'EOF'
---
status: approved
---
# decision
EOF
  git add docs

  run ./scripts/check-status

  [ "$status" -eq 0 ]
}

@test "a milestone status value is invalid for decisions and vice versa" {
  mkdir -p docs/decisions
  cat >docs/decisions/2026-01-01-example.md <<'EOF'
---
status: in_progress
---
# decision
EOF
  git add docs

  run ./scripts/check-status

  [ "$status" -eq 1 ]
  [[ $output == *'invalid status "in_progress" in docs/decisions/2026-01-01-example.md'* ]]
}

@test "directories outside the tracked list are ignored" {
  mkdir -p docs/architecture
  echo "no frontmatter needed here" >docs/architecture/core.md
  git add docs

  run ./scripts/check-status

  [ "$status" -eq 0 ]
}
