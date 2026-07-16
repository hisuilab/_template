#!/usr/bin/env bats

setup() {
  repo_root="$(cd "$BATS_TEST_DIRNAME/../../.." && pwd)" || return 1
}

# flake.nix の git-hooks ブロック内に含まれるフック名を抽出する
git_hooks_block() {
  awk '/hooks = git-hooks\.lib/,/^          };/' "$repo_root/flake.nix"
}

@test "check-status hook is declared in git-hooks.nix configuration" {
  run bash -c "git_hooks_block() { awk '/hooks = git-hooks\.lib/,/^          };/' \"$repo_root/flake.nix\"; }; git_hooks_block | grep -c 'check-status'"
  [ "$output" -ge 1 ]
}

@test "check-encoding hook is declared in git-hooks.nix configuration" {
  run bash -c "git_hooks_block() { awk '/hooks = git-hooks\.lib/,/^          };/' \"$repo_root/flake.nix\"; }; git_hooks_block | grep -c 'check-encoding'"
  [ "$output" -ge 1 ]
}
