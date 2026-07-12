#!/usr/bin/env bats

setup() {
  repo_root="$(cd "$BATS_TEST_DIRNAME/../../.." && pwd)" || return 1
  result_path="$(nix build "$repo_root#" --no-link --print-out-paths 2>/dev/null)" || true
}

@test "nix build .# succeeds" {
  run nix build "$repo_root#" --no-link --print-out-paths
  [ "$status" -eq 0 ]
}

@test "nix build .# produces an executable _template binary" {
  [ -n "$result_path" ] || skip "nix build failed"
  [ -x "$result_path/bin/_template" ]
}

@test "_template binary prints help without error" {
  [ -n "$result_path" ] || skip "nix build failed"
  run "$result_path/bin/_template" generate --help
  [ "$status" -eq 0 ]
}
