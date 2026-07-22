#!/usr/bin/env bats
# Each @test runs in an isolated subshell, so mock state must be test-local.
# shellcheck disable=SC2030,SC2031

bats_require_minimum_version 1.5.0

setup() {
  repo_root="$(cd "$BATS_TEST_DIRNAME/../../.." && pwd)"
  helper="$repo_root/scripts/worktree-safety"
  test_dir="$(mktemp -d)"
  manager="$test_dir/example-main"
  mkdir -p "$manager/tmp"
  git -C "$manager" init -q -b main
  git -C "$manager" config user.email test@example.com
  git -C "$manager" config user.name test
  git -C "$manager" commit -q --allow-empty -m "chore: initialize test repository"
  printf 'tmp/\n' >>"$manager/.git/info/exclude"
  mock_bin="$test_dir/bin"
  mkdir -p "$mock_bin"
  cat >"$mock_bin/gh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
case "${1:-} ${2:-}" in
"repo view")
  [ "$#" -eq 4 ] && [ "$3" = "--json" ] && [ "$4" = "nameWithOwner" ] || exit 3
  printf '{"nameWithOwner":"%s"}\n' "${MOCK_REPO:-owner/example}"
  ;;
"pr view")
  [[ ${3:-} =~ ^[1-9][0-9]*$ ]] || exit 3
  [ "${4:-}" = "--repo" ] && [ "${5:-}" = "${MOCK_REPO:-owner/example}" ] || exit 3
  [ "${6:-}" = "--json" ] && [ "${7:-}" = "state,headRefOid,headRefName" ] || exit 3
  head_sha="${MOCK_PR_HEAD:-$(git -C "$MOCK_MANAGER" rev-parse "$MOCK_PR_BRANCH")}"
  printf '{"state":"%s","headRefOid":"%s","headRefName":"%s"}\n' \
    "${MOCK_PR_STATE:-MERGED}" "$head_sha" "${MOCK_PR_BRANCH:-feat/issue-999-contract}"
  ;;
*)
  exit 2
  ;;
esac
EOF
  chmod +x "$mock_bin/gh"
  export PATH="$mock_bin:$PATH"
  export MOCK_MANAGER="$manager"
  export MOCK_PR_BRANCH="feat/issue-999-contract"
}

teardown() {
  rm -rf "$test_dir"
}

plan_create() {
  "$helper" plan-create \
    --manager-root "$manager" \
    --issue 999 \
    --branch feat/issue-999-contract \
    --path "$test_dir/example-issue-999" \
    --tool codex
}

apply_create() {
  local plan base_sha plan_token
  plan="$(plan_create)"
  base_sha="$(jq -r '.base_sha' <<<"$plan")"
  plan_token="$(jq -r '.plan_token' <<<"$plan")"
  "$helper" apply-create \
    --manager-root "$manager" \
    --issue 999 \
    --branch feat/issue-999-contract \
    --path "$test_dir/example-issue-999" \
    --tool codex \
    --approved-base "$base_sha" \
    --approved-plan "$plan_token"
}

plan_cleanup() {
  "$helper" plan-cleanup \
    --manager-root "$manager" \
    --issue 999 \
    --pr 42
}

@test "plan-create emits a normalized JSON plan" {
  run plan_create

  [ "$status" -eq 0 ]
  [ "$(jq -r '.operation' <<<"$output")" = "create" ]
  [ "$(jq -r '.issue' <<<"$output")" = "999" ]
  [ "$(jq -r '.worktree_count' <<<"$output")" = "0" ]
  [ "$(jq -r '.base_sha' <<<"$output")" = "$(git -C "$manager" rev-parse main)" ]
}

@test "plan-create rejects a path outside the manager parent" {
  mkdir -p "$test_dir/nested"

  run "$helper" plan-create \
    --manager-root "$manager" \
    --issue 999 \
    --branch feat/issue-999-contract \
    --path "$test_dir/nested/example-issue-999" \
    --tool codex

  [ "$status" -ne 0 ]
  [[ $output == *"expected sibling path"* ]]
}

@test "plan-create rejects an unknown registry version" {
  printf '{"version":2,"worktrees":{}}\n' >"$manager/tmp/worktrees.json"

  run plan_create

  [ "$status" -ne 0 ]
  [[ $output == *"unsupported registry version"* ]]
}

@test "plan-create counts unregistered issue worktrees toward the limit" {
  git -C "$manager" worktree add -q -b feat/issue-1-test "$test_dir/example-issue-1" main
  git -C "$manager" worktree add -q -b feat/issue-2-test "$test_dir/example-issue-2" main
  git -C "$manager" worktree add -q -b feat/issue-3-test "$test_dir/example-issue-3" main

  run plan_create

  [ "$status" -ne 0 ]
  [[ $output == *"worktree limit reached"* ]]
}

@test "apply-create creates worktree phase state and registry entry" {
  run apply_create

  [ "$status" -eq 0 ]
  [ -d "$test_dir/example-issue-999" ]
  [ "$(jq -r '.current' "$test_dir/example-issue-999/tmp/issue-999/phase-state.json")" = "null" ]
  [ "$(jq -r '.worktrees["issue-999"].assigned_tool' "$manager/tmp/worktrees.json")" = "codex" ]
}

@test "apply-create rejects a changed approved base" {
  create_plan="$(plan_create)"
  approved_base="$(jq -r '.base_sha' <<<"$create_plan")"
  approved_plan="$(jq -r '.plan_token' <<<"$create_plan")"
  git -C "$manager" commit -q --allow-empty -m "chore: advance main"

  run "$helper" apply-create \
    --manager-root "$manager" \
    --issue 999 \
    --branch feat/issue-999-contract \
    --path "$test_dir/example-issue-999" \
    --tool codex \
    --approved-base "$approved_base" \
    --approved-plan "$approved_plan"

  [ "$status" -ne 0 ]
  [[ $output == *"approved base changed"* ]]
  [ ! -e "$test_dir/example-issue-999" ]
}

@test "apply-create rejects a changed approved plan" {
  create_plan="$(plan_create)"
  approved_base="$(jq -r '.base_sha' <<<"$create_plan")"
  approved_plan="$(jq -r '.plan_token' <<<"$create_plan")"

  run "$helper" apply-create \
    --manager-root "$manager" \
    --issue 999 \
    --branch feat/issue-999-contract \
    --path "$test_dir/example-issue-999" \
    --tool claude \
    --approved-base "$approved_base" \
    --approved-plan "$approved_plan"

  [ "$status" -ne 0 ]
  [[ $output == *"approved create plan changed"* ]]
  [ ! -e "$test_dir/example-issue-999" ]
}

@test "plan-cleanup rejects a dirty worktree" {
  apply_create >/dev/null
  printf 'dirty\n' >"$test_dir/example-issue-999/untracked.txt"

  run plan_cleanup

  [ "$status" -ne 0 ]
  [[ $output == *"worktree is not clean"* ]]
}

@test "plan-cleanup rejects detached HEAD" {
  apply_create >/dev/null
  git -C "$test_dir/example-issue-999" switch -q --detach

  run plan_cleanup

  [ "$status" -ne 0 ]
  [[ $output == *"detached HEAD"* ]]
}

@test "plan-cleanup rejects a PR head mismatch" {
  apply_create >/dev/null
  MOCK_PR_HEAD=0000000000000000000000000000000000000000
  export MOCK_PR_HEAD

  run plan_cleanup

  [ "$status" -ne 0 ]
  [[ $output == *"PR head SHA mismatch"* ]]
}

@test "apply-cleanup removes worktree branch and registry entry" {
  apply_create >/dev/null
  cleanup_plan="$(plan_cleanup)"
  head_sha="$(jq -r '.head_sha' <<<"$cleanup_plan")"
  approved_plan="$(jq -r '.plan_token' <<<"$cleanup_plan")"

  run "$helper" apply-cleanup \
    --manager-root "$manager" \
    --issue 999 \
    --pr 42 \
    --approved-head "$head_sha" \
    --approved-plan "$approved_plan"

  [ "$status" -eq 0 ]
  [ ! -e "$test_dir/example-issue-999" ]
  run ! git -C "$manager" show-ref --verify --quiet refs/heads/feat/issue-999-contract
  [ "$(jq -r '.worktrees | has("issue-999")' "$manager/tmp/worktrees.json")" = "false" ]
}

@test "apply-cleanup resumes after worktree removal" {
  apply_create >/dev/null
  cleanup_plan="$(plan_cleanup)"
  head_sha="$(jq -r '.head_sha' <<<"$cleanup_plan")"
  git -C "$manager" worktree remove -- "$test_dir/example-issue-999"
  cleanup_plan="$(plan_cleanup)"
  approved_plan="$(jq -r '.plan_token' <<<"$cleanup_plan")"

  run "$helper" apply-cleanup \
    --manager-root "$manager" \
    --issue 999 \
    --pr 42 \
    --approved-head "$head_sha" \
    --approved-plan "$approved_plan"

  [ "$status" -eq 0 ]
  run ! git -C "$manager" show-ref --verify --quiet refs/heads/feat/issue-999-contract
  [ "$(jq -r '.worktrees | has("issue-999")' "$manager/tmp/worktrees.json")" = "false" ]
}

@test "apply-cleanup rejects a changed approved plan" {
  apply_create >/dev/null
  cleanup_plan="$(plan_cleanup)"
  head_sha="$(jq -r '.head_sha' <<<"$cleanup_plan")"
  approved_plan="$(jq -r '.plan_token' <<<"$cleanup_plan")"

  run "$helper" apply-cleanup \
    --manager-root "$manager" \
    --issue 999 \
    --pr 43 \
    --approved-head "$head_sha" \
    --approved-plan "$approved_plan"

  [ "$status" -ne 0 ]
  [[ $output == *"approved cleanup plan changed"* ]]
  [ -d "$test_dir/example-issue-999" ]
}

@test "apply-cleanup rechecks GitHub state after approval" {
  apply_create >/dev/null
  cleanup_plan="$(plan_cleanup)"
  head_sha="$(jq -r '.head_sha' <<<"$cleanup_plan")"
  approved_plan="$(jq -r '.plan_token' <<<"$cleanup_plan")"
  MOCK_PR_STATE=OPEN
  export MOCK_PR_STATE

  run "$helper" apply-cleanup \
    --manager-root "$manager" \
    --issue 999 \
    --pr 42 \
    --approved-head "$head_sha" \
    --approved-plan "$approved_plan"

  [ "$status" -ne 0 ]
  [[ $output == *"PR is not merged"* ]]
  [ -d "$test_dir/example-issue-999" ]
}

@test "apply-cleanup rejects a changed GitHub repository" {
  apply_create >/dev/null
  cleanup_plan="$(plan_cleanup)"
  head_sha="$(jq -r '.head_sha' <<<"$cleanup_plan")"
  approved_plan="$(jq -r '.plan_token' <<<"$cleanup_plan")"
  MOCK_REPO=owner/other
  export MOCK_REPO

  run "$helper" apply-cleanup \
    --manager-root "$manager" \
    --issue 999 \
    --pr 42 \
    --approved-head "$head_sha" \
    --approved-plan "$approved_plan"

  [ "$status" -ne 0 ]
  [[ $output == *"approved cleanup plan changed"* ]]
  [ -d "$test_dir/example-issue-999" ]
}

@test "apply-cleanup compare-deletes an unmerged local branch" {
  apply_create >/dev/null
  git -C "$test_dir/example-issue-999" commit -q --allow-empty -m "feat: add squashed change"
  cleanup_plan="$(plan_cleanup)"
  head_sha="$(jq -r '.head_sha' <<<"$cleanup_plan")"
  approved_plan="$(jq -r '.plan_token' <<<"$cleanup_plan")"
  [ "$(jq -r '.force_branch' <<<"$cleanup_plan")" = "true" ]

  run "$helper" apply-cleanup \
    --manager-root "$manager" \
    --issue 999 \
    --pr 42 \
    --approved-head "$head_sha" \
    --approved-plan "$approved_plan"

  [ "$status" -eq 0 ]
  run ! git -C "$manager" show-ref --verify --quiet refs/heads/feat/issue-999-contract
}

@test "plan-cleanup rejects a non-merged GitHub PR" {
  apply_create >/dev/null
  MOCK_PR_STATE=OPEN
  export MOCK_PR_STATE

  run plan_cleanup

  [ "$status" -ne 0 ]
  [[ $output == *"PR is not merged"* ]]
}

@test "plan-cleanup rejects a GitHub PR head branch mismatch" {
  apply_create >/dev/null
  MOCK_PR_BRANCH=feat/issue-998-other
  MOCK_PR_HEAD="$(git -C "$manager" rev-parse feat/issue-999-contract)"
  export MOCK_PR_BRANCH MOCK_PR_HEAD

  run plan_cleanup

  [ "$status" -ne 0 ]
  [[ $output == *"PR head branch mismatch"* ]]
}

@test "plan-cleanup rejects a remote-tracking mismatch" {
  apply_create >/dev/null
  git -C "$manager" commit -q --allow-empty -m "chore: advance remote fixture"
  git -C "$manager" update-ref refs/remotes/origin/feat/issue-999-contract main
  git -C "$manager" remote add origin "$test_dir/unused-remote"
  git -C "$manager" branch --set-upstream-to=origin/feat/issue-999-contract feat/issue-999-contract

  run plan_cleanup

  [ "$status" -ne 0 ]
  [[ $output == *"remote-tracking SHA mismatch"* ]]
}

@test "assign updates the tool under the registry lock" {
  apply_create >/dev/null

  run "$helper" assign --manager-root "$manager" --issue 999 --tool claude

  [ "$status" -eq 0 ]
  [ "$(jq -r '.worktrees["issue-999"].assigned_tool' "$manager/tmp/worktrees.json")" = "claude" ]
  [ ! -d "$manager/tmp/worktrees.lock" ]
}

@test "lock-status identifies and reclaim-lock removes a stale owner" {
  mkdir -p "$manager/tmp/worktrees.lock"
  host_name="$(hostname)"
  cat >"$manager/tmp/worktrees.lock/owner.json" <<EOF
{"token":"stale-token","host":"$host_name","pid":999999,"process_start":"never","operation":"test","agent":"bats","acquired_at":"2026-07-22T00:00:00Z"}
EOF

  run "$helper" lock-status --manager-root "$manager"
  [ "$status" -eq 0 ]
  [ "$(jq -r '.state' <<<"$output")" = "stale" ]

  run "$helper" reclaim-lock --manager-root "$manager" --owner-token wrong-token
  [ "$status" -ne 0 ]
  [ -d "$manager/tmp/worktrees.lock" ]

  run "$helper" reclaim-lock --manager-root "$manager" --owner-token stale-token
  [ "$status" -eq 0 ]
  [ ! -d "$manager/tmp/worktrees.lock" ]
}
