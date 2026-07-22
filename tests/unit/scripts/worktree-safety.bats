#!/usr/bin/env bats

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
  local base_sha
  base_sha="$(git -C "$manager" rev-parse main)"
  "$helper" apply-create \
    --manager-root "$manager" \
    --issue 999 \
    --branch feat/issue-999-contract \
    --path "$test_dir/example-issue-999" \
    --tool codex \
    --approved-base "$base_sha"
}

plan_cleanup() {
  local head_sha
  head_sha="$(git -C "$manager" rev-parse feat/issue-999-contract)"
  "$helper" plan-cleanup \
    --manager-root "$manager" \
    --issue 999 \
    --pr-state MERGED \
    --pr-head "$head_sha"
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
  approved_base="$(git -C "$manager" rev-parse main)"
  git -C "$manager" commit -q --allow-empty -m "chore: advance main"

  run "$helper" apply-create \
    --manager-root "$manager" \
    --issue 999 \
    --branch feat/issue-999-contract \
    --path "$test_dir/example-issue-999" \
    --tool codex \
    --approved-base "$approved_base"

  [ "$status" -ne 0 ]
  [[ $output == *"approved base changed"* ]]
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

  run "$helper" plan-cleanup \
    --manager-root "$manager" \
    --issue 999 \
    --pr-state MERGED \
    --pr-head 0000000000000000000000000000000000000000

  [ "$status" -ne 0 ]
  [[ $output == *"PR head SHA mismatch"* ]]
}

@test "apply-cleanup removes worktree branch and registry entry" {
  apply_create >/dev/null
  head_sha="$(git -C "$manager" rev-parse feat/issue-999-contract)"

  run "$helper" apply-cleanup \
    --manager-root "$manager" \
    --issue 999 \
    --pr-state MERGED \
    --pr-head "$head_sha" \
    --approved-head "$head_sha"

  [ "$status" -eq 0 ]
  [ ! -e "$test_dir/example-issue-999" ]
  run ! git -C "$manager" show-ref --verify --quiet refs/heads/feat/issue-999-contract
  [ "$(jq -r '.worktrees | has("issue-999")' "$manager/tmp/worktrees.json")" = "false" ]
}

@test "apply-cleanup resumes after worktree removal" {
  apply_create >/dev/null
  head_sha="$(git -C "$manager" rev-parse feat/issue-999-contract)"
  git -C "$manager" worktree remove -- "$test_dir/example-issue-999"

  run "$helper" apply-cleanup \
    --manager-root "$manager" \
    --issue 999 \
    --pr-state MERGED \
    --pr-head "$head_sha" \
    --approved-head "$head_sha"

  [ "$status" -eq 0 ]
  run ! git -C "$manager" show-ref --verify --quiet refs/heads/feat/issue-999-contract
  [ "$(jq -r '.worktrees | has("issue-999")' "$manager/tmp/worktrees.json")" = "false" ]
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
