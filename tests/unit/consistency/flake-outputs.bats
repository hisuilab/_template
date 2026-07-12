#!/usr/bin/env bats

setup_file() {
  local repo_root
  repo_root="$(cd "$BATS_TEST_DIRNAME/../../.." && pwd)"
  echo "$repo_root" >"$BATS_SUITE_TMPDIR/repo_root"
  local result_path
  result_path="$(nix build "$repo_root#" --no-link --print-out-paths 2>"$BATS_SUITE_TMPDIR/nix_build_err")" || {
    echo "nix build failed: $(cat "$BATS_SUITE_TMPDIR/nix_build_err")" >&2
    return 1
  }
  echo "$result_path" >"$BATS_SUITE_TMPDIR/result_path"
}

setup() {
  repo_root="$(cat "$BATS_SUITE_TMPDIR/repo_root")"
  result_path="$(cat "$BATS_SUITE_TMPDIR/result_path")"
}

@test "nix build .# produces an executable _template binary" {
  [ -x "$result_path/bin/_template" ]
}

@test "_template binary prints help without error" {
  run "$result_path/bin/_template" generate --help
  [ "$status" -eq 0 ]
}
