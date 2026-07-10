#!/usr/bin/env bats

setup() {
  repo_root="$(cd "$BATS_TEST_DIRNAME/../../.." && pwd)" || return 1
}

# flake.nix の devShell `packages = [ ... ];` ブロックから、宣言されているツール名を1行1件で抽出する。
devshell_packages() {
  awk '/packages = \[/{flag=1; next} /\];/{flag=0} flag' "$repo_root/flake.nix" |
    sed -E 's/^ *pkgs\.//; s/ *;? *$//' |
    sed -E 's#treefmtEval\.\$\{system\}\.config\.build\.wrapper#treefmt#' |
    sed -E 's/^ +//; s/ +$//' |
    sed '/^$/d'
}

# justfile / scripts/precommit / scripts/check-readme の `# requires: a, b` コメントから要求ツール名を1行1件で抽出する。
required_tools() {
  grep -hoE '# requires: .*' "$repo_root/justfile" "$repo_root/scripts/precommit" "$repo_root/scripts/check-readme" |
    sed -E 's/# requires: //' |
    tr ',' '\n' |
    sed -E 's/^ +//; s/ +$//' |
    sed '/^$/d'
}

@test "every tool in a '# requires:' annotation is declared in the devShell packages" {
  mapfile -t packages < <(devshell_packages)

  while IFS= read -r tool; do
    found=0
    for package in "${packages[@]}"; do
      if [ "$package" = "$tool" ]; then
        found=1
        break
      fi
    done
    if [ "$found" -ne 1 ]; then
      echo "missing devShell package for required tool: $tool"
      return 1
    fi
  done < <(required_tools)
}
