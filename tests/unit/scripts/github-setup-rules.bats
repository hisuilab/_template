#!/usr/bin/env bats

setup() {
  repo_root="$(cd "$BATS_TEST_DIRNAME/../../.." && pwd)"
  test_dir="$(mktemp -d)"

  # Mirror the directory structure of a generated project
  mkdir -p "$test_dir/scripts"
  mkdir -p "$test_dir/.github/rulesets"
  mkdir -p "$test_dir/bin"

  cp "$repo_root/template/parts/features/github-rulesets/payload/scripts/github-setup-rules" \
    "$test_dir/scripts/github-setup-rules"
  cp "$repo_root/template/parts/features/github-rulesets/payload/dot-github/rulesets/solo.json" \
    "$test_dir/.github/rulesets/solo.json"
  cp "$repo_root/template/parts/features/github-rulesets/payload/dot-github/rulesets/team.json" \
    "$test_dir/.github/rulesets/team.json"

  # Initialize git so git rev-parse --show-toplevel works from test_dir
  git -C "$test_dir" init -q

  cd "$test_dir" || return 1

  # Prepend mock bin dir to PATH for this test
  export PATH="$test_dir/bin:$PATH"
}

teardown() {
  rm -rf "$test_dir"
}

# --- Mock helpers ---

_mock_gh_success() {
  cat >"$test_dir/bin/gh" <<'MOCK'
#!/usr/bin/env bash
if [[ "$*" == *"auth status"* ]]; then exit 0; fi
if [[ "$*" == *"repo view"* ]]; then echo "hisuilab/test"; exit 0; fi
if [[ "$*" == *"-X POST"* ]] || [[ "$*" == *"-X PUT"* ]]; then
  echo '{"id":1}'
  exit 0
fi
if [[ "$*" == *"rulesets"* ]]; then echo "[]"; exit 0; fi
exit 0
MOCK
  chmod +x "$test_dir/bin/gh"
}

_mock_gh_get_403() {
  cat >"$test_dir/bin/gh" <<'MOCK'
#!/usr/bin/env bash
if [[ "$*" == *"auth status"* ]]; then exit 0; fi
if [[ "$*" == *"repo view"* ]]; then echo "hisuilab/test"; exit 0; fi
if [[ "$*" == *"rulesets"* ]]; then
  echo "Upgrade to GitHub Pro or make this repository public to enable this feature." >&2
  exit 1
fi
exit 0
MOCK
  chmod +x "$test_dir/bin/gh"
}

_mock_gh_post_403() {
  cat >"$test_dir/bin/gh" <<'MOCK'
#!/usr/bin/env bash
if [[ "$*" == *"auth status"* ]]; then exit 0; fi
if [[ "$*" == *"repo view"* ]]; then echo "hisuilab/test"; exit 0; fi
if [[ "$*" == *"-X POST"* ]] || [[ "$*" == *"-X PUT"* ]]; then
  echo "Upgrade to GitHub Pro or make this repository public to enable this feature." >&2
  exit 1
fi
if [[ "$*" == *"rulesets"* ]]; then echo "[]"; exit 0; fi
exit 0
MOCK
  chmod +x "$test_dir/bin/gh"
}

# --- Pass cases ---

@test "unknown preset: exits 1 with error message" {
  _mock_gh_success

  run bash scripts/github-setup-rules no_such_preset

  [ "$status" -eq 1 ]
  [[ $output == *"error"* ]]
}

@test "success with no existing ruleset: exits 0 and writes rules-preset file" {
  _mock_gh_success

  run bash scripts/github-setup-rules solo

  [ "$status" -eq 0 ]
  [ -f ".github/rules-preset" ]
  grep -q "solo" ".github/rules-preset"
}

@test "success with team preset: exits 0 and writes team to rules-preset" {
  _mock_gh_success

  run bash scripts/github-setup-rules team

  [ "$status" -eq 0 ]
  grep -q "team" ".github/rules-preset"
}

# --- 403 graceful handling (RED until #44 fix is applied) ---

@test "rulesets GET 403: exits 0 with warning instead of crashing" {
  _mock_gh_get_403

  run bash scripts/github-setup-rules solo

  [ "$status" -eq 0 ]
  [[ $output == *"arning"* ]] || [[ $output == *"kipping"* ]]
}

@test "rulesets POST 403: exits 0 with warning instead of crashing" {
  _mock_gh_post_403

  run bash scripts/github-setup-rules solo

  [ "$status" -eq 0 ]
  [[ $output == *"arning"* ]] || [[ $output == *"kipping"* ]]
}
