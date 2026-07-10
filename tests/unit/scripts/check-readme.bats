#!/usr/bin/env bats

setup() {
  repo_root="$(cd "$BATS_TEST_DIRNAME/../../.." && pwd)"
  test_dir="$(mktemp -d)"
  mkdir -p "$test_dir/scripts"
  ln -s "$repo_root/scripts/check-readme" "$test_dir/scripts/check-readme"
  cd "$test_dir" || return 1
  git init -q
  git config user.email test@example.com
  git config user.name test
}

teardown() {
  rm -rf "$test_dir"
}

write_readme() {
  cat >"$1" <<'EOF'
# title

## 1. 概要

説明

## 2. 責任

- 保持するもの: x

## 3. 責任外

- y
EOF
}

@test "directory with a tracked file but no README.md fails" {
  mkdir -p pkg
  echo "x" >pkg/file.txt
  write_readme README.md
  git add pkg README.md

  run ./scripts/check-readme

  [ "$status" -eq 1 ]
  [[ $output == *"missing README.md: pkg/README.md"* ]]
}

@test "README.md missing required sections fails" {
  mkdir -p pkg
  echo "x" >pkg/file.txt
  echo "# title" >pkg/README.md
  write_readme README.md
  git add pkg README.md

  run ./scripts/check-readme

  [ "$status" -eq 1 ]
  [[ $output == *"'## 1. 概要' section: pkg/README.md"* ]]
  [[ $output == *"'## 2. 責任' section: pkg/README.md"* ]]
  [[ $output == *"'## 3. 責任外' section: pkg/README.md"* ]]
}

@test "README.md containing a table of contents fails" {
  mkdir -p pkg
  cat >pkg/README.md <<'EOF'
# title

## 目次

- [1. 概要](#1-概要)

## 1. 概要

説明

## 2. 責任

- 保持するもの: x

## 3. 責任外

- y
EOF
  echo "x" >pkg/file.txt
  write_readme README.md
  git add pkg README.md

  run ./scripts/check-readme

  [ "$status" -eq 1 ]
  [[ $output == *"must not contain a table of contents"* ]]
  [[ $output == *"pkg/README.md"* ]]
}

@test "properly structured README.md passes" {
  mkdir -p pkg
  echo "x" >pkg/file.txt
  write_readme pkg/README.md
  write_readme README.md
  git add pkg README.md

  run ./scripts/check-readme

  [ "$status" -eq 0 ]
}

@test "directory listed in .readmeignore is exempt" {
  mkdir -p pkg
  echo "x" >pkg/file.txt
  write_readme README.md
  printf 'pkg/\n' >.readmeignore
  git add pkg README.md .readmeignore

  run ./scripts/check-readme

  [ "$status" -eq 0 ]
}

@test "root README.md is required but exempt from the section and table-of-contents checks" {
  cat >README.md <<'EOF'
# title

## 目次

- [1. 概要](#1-概要)

## 1. 概要

説明
EOF
  git add README.md

  run ./scripts/check-readme

  [ "$status" -eq 0 ]
}

@test "missing root README.md fails" {
  echo "x" >file.txt
  git add file.txt

  run ./scripts/check-readme

  [ "$status" -eq 1 ]
  [[ $output == *"missing README.md: README.md"* ]]
}
