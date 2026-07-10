#!/usr/bin/env bats

setup() {
  repo_root="$(cd "$BATS_TEST_DIRNAME/../../.." && pwd)"
  test_dir="$(mktemp -d)"
  mkdir -p "$test_dir/scripts"
  ln -s "$repo_root/scripts/precommit" "$test_dir/scripts/precommit"
  cd "$test_dir" || return 1
}

teardown() {
  rm -rf "$test_dir"
}

@test "not a git repository: skips checks and exits 0" {
  run ./scripts/precommit

  [ "$status" -eq 0 ]
  [[ $output == *"Not a git repository yet"* ]]
}

@test "git repository with no checkable files: exits 0 without invoking prek" {
  git init -q

  excludes_file="$(mktemp)"
  echo "scripts/" >"$excludes_file"
  git config core.excludesFile "$excludes_file"

  run ./scripts/precommit

  [ "$status" -eq 0 ]
  [[ $output == *"No files to check."* ]]
}

@test "git repository with files: invokes prek with the discovered files" {
  git init -q
  echo "hello" >README.md

  mkdir -p bin
  cat >bin/prek <<'EOF'
#!/usr/bin/env bash
echo "prek called with: $*" >"$PREK_LOG"
EOF
  chmod +x bin/prek

  export PREK_LOG="$test_dir/prek.log"
  export PATH="$test_dir/bin:$PATH"

  run ./scripts/precommit

  [ "$status" -eq 0 ]
  grep -q "scripts/precommit" "$PREK_LOG"
  grep -q "README.md" "$PREK_LOG"
  grep -q -- "--show-diff-on-failure" "$PREK_LOG"
}
