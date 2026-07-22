#!/usr/bin/env bats

setup() {
  repo_root="$(cd "$BATS_TEST_DIRNAME/../../.." && pwd)"
}

@test "manage triage command is documented consistently" {
  manage_doc="$repo_root/agent-workflow/commands/manage.md"
  permissions_doc="$repo_root/agent-workflow/rules/command-permissions.md"
  commands_readme="$repo_root/agent-workflow/commands/README.md"

  # shellcheck disable=SC2016
  grep -q '^権限: .*`/manage:triage`.*read-only' "$manage_doc"
  grep -q '^- \[.*manage:triage.*\]' "$manage_doc"
  grep -q '^## [0-9]\+\. manage:triage$' "$manage_doc"
  # shellcheck disable=SC2016
  grep -Fq '| `/manage:triage` | read-only |' "$permissions_doc"
  # shellcheck disable=SC2016
  grep -q '`manage.md`: .*triage' "$commands_readme"
}
