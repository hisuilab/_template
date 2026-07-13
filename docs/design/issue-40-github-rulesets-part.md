---
status: approved
proposed_at: 2026-07-13
approved_at: 2026-07-13
approved_by: PM
approval_ref: "https://github.com/hisuilab/_template/issues/40"
implemented_at: 2026-07-13
related: "#40"
---

# 設計提案: features/github-rulesets Part 追加

## 目次

- [1. 問題](#1-問題)
- [2. 対象範囲](#2-対象範囲)
- [3. 選択肢](#3-選択肢)
- [4. 設計案](#4-設計案)
- [5. 失敗とロールバック](#5-失敗とロールバック)
- [6. 検証](#6-検証)
- [7. 未解決事項](#7-未解決事項)

## 1. 問題

プロジェクト生成後の GitHub branch protection 設定は手動作業であり、設定内容が git で追跡されない。プロジェクトごとに設定のばらつきが生じ、再現コストが高い。

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| `features/github-rulesets` Part の新規追加 | Organization リポジトリ対応 |
| `solo.json` / `team.json` ルールセットテンプレート | `bypass_actors` の設定 |
| `scripts/github-setup-rules` 適用スクリプト | `github-setup-labels` 等の将来拡張 |
| `.github/rules-preset` プリセット状態ファイル | GitHub Actions 等の他の `.github/` ファイル |
| 5 つの `github-*` just レシピを base justfile に追加 | CI job 名のパラメータ化（将来 Issue） |
| 全 3 Profile（`small-cli` / `small-web-api` / `small-library`）への組み込み |  |
| base flake.nix への `pkgs.gh` / `pkgs.jq` 追加 |  |

## 3. 選択肢

| # | 選択肢 | 採否 |
| --- | --- | --- |
| A | JSON テンプレート + 適用スクリプトを Part として提供 | 採用 |
| B | `docs/development/` にドキュメントのみ記載 | 不採用（再現性がない） |

プリセット状態管理の方法は以下から選択し、B を採用しました。

| # | 方法 | 採否 |
| --- | --- | --- |
| A | `github-setup-rules` 実行引数をユーザーが毎回指定 | 不採用（`github-setup` がプリセットを把握できない） |
| B | `.github/rules-preset` ファイルに現在のプリセット名を記録 | 採用（git で追跡・チーム共有可能） |

## 4. 設計案

### ファイル構成

```text
template/parts/features/github-rulesets/
├── part.toml
├── README.md
└── payload/
    ├── dot-github/
    │   ├── rules-preset           ← 初期値: "solo"
    │   └── rulesets/
    │       ├── solo.json
    │       └── team.json
    └── scripts/
        └── github-setup-rules    ← 旧: setup-github
```

`dot-github/` プレフィックスは planner.py が除去するため、生成先では `.github/` として出力されます。

### `part.toml`

```toml
[part]
id = "features/github-rulesets"
requires = ["base"]
conflicts = []
```

### プリセット状態管理（`.github/rules-preset`）

`github-setup` が「現在どのプリセットか」を知るための状態ファイルです。

- 生成時: Part が `solo` を初期値として生成します
- `github-setup-rules [preset]` 実行後: スクリプトがこのファイルを更新します
- `github-setup` 実行時: このファイルを読んでプリセットを決定します
- git で追跡するため、チームメンバーが clone しても同じプリセットが適用されます

### ルールセットの内容

**`solo.json`** — 個人開発向け。PR 必須・CI 必須・force push/削除禁止。

```json
{
  "name": "main-protection",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "include": ["refs/heads/main"],
      "exclude": []
    }
  },
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 0,
        "require_code_owner_review": true,
        "dismiss_stale_reviews_on_push": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": false
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": false,
        "required_status_checks": [{ "context": "Verify" }]
      }
    }
  ]
}
```

**`team.json`** — チーム向け。solo に加え、承認1件必須・stale review 無効化・スレッド解決必須。

```json
{
  "name": "main-protection",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "include": ["refs/heads/main"],
      "exclude": []
    }
  },
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 1,
        "require_code_owner_review": true,
        "dismiss_stale_reviews_on_push": true,
        "require_last_push_approval": false,
        "required_review_thread_resolution": true
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": false,
        "required_status_checks": [{ "context": "Verify" }]
      }
    }
  ]
}
```

### base justfile — 5 レシピ

```justfile
# =============================================================================
# GitHub — repository setup and status
# =============================================================================

# [初回のみ・冪等でない] GitHub リポジトリを作成し全設定を適用する
# 2回目以降は github-setup を使ってください
github-init visibility="private":
    #!/usr/bin/env bash
    set -euo pipefail
    gh auth status > /dev/null 2>&1 \
      || { echo "error: gh not authenticated. Run: gh auth login" >&2; exit 1; }
    git rev-parse HEAD > /dev/null 2>&1 \
      || { echo "error: no commits yet. Run: git add -A && git commit -m 'init'" >&2; exit 1; }
    if git remote get-url origin > /dev/null 2>&1; then
      echo "error: origin already set. Use: git push -u origin main && just github-setup" >&2
      exit 1
    fi
    gh repo create \
      "$(gh api user --jq .login)/{{project_name}}" \
      --{{visibility}} --source=. --remote=origin --push
    just github-setup
    echo "✓ {{project_name}} initialized on GitHub"

# 全 GitHub 設定を適用する（.github/rules-preset に従い冪等）
github-setup:
    #!/usr/bin/env bash
    set -euo pipefail
    preset="$(cat .github/rules-preset 2>/dev/null || echo solo)"
    just github-setup-rules "$preset"

# Rules プリセットを適用または更新し .github/rules-preset を記録する（default: solo）
github-setup-rules preset="solo":
    bash scripts/github-setup-rules {{preset}}

# 全 GitHub 設定の現状を表示する
github-status:
    just github-rules-status

# 現在 GitHub に適用されている Rules を表示する
github-rules-status:
    #!/usr/bin/env bash
    set -euo pipefail
    if ! gh repo view --json nameWithOwner -q .nameWithOwner > /dev/null 2>&1; then
      echo "No GitHub remote configured. Run: just github-init"
      exit 0
    fi
    repo="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
    preset="$(cat .github/rules-preset 2>/dev/null || echo '(unknown)')"
    echo "=== Rules: ${repo} (preset: ${preset}) ==="
    gh api "repos/${repo}/rulesets" \
      --header "X-GitHub-Api-Version: 2022-11-28" \
      | jq '.[] | {id, name, enforcement, updated_at}'
```

**対称構造:** `github-setup → github-setup-rules`、`github-status → github-rules-status` の組で、将来の `github-setup-labels` 等は各 orchestrator に1行追加するだけで対応できます。

### `scripts/github-setup-rules`

旧 `scripts/setup-github` をリネームし、auth チェック・パス修正・rules-preset 書き込みを追加します。

```sh
#!/usr/bin/env bash
# requires: gh, jq
# Apply or update a GitHub Rules preset for this repository.
# Usage: bash scripts/github-setup-rules [solo|team]  (default: solo)
# Safe to re-run (idempotent). Updates .github/rules-preset after apply.
set -euo pipefail

if ! gh auth status &>/dev/null; then
  echo "error: gh is not authenticated. Run: gh auth login" >&2
  exit 1
fi

preset="${1:-solo}"
repo_root="$(git rev-parse --show-toplevel)"
ruleset_file="$repo_root/.github/rulesets/${preset}.json"
preset_file="$repo_root/.github/rules-preset"
api_version="X-GitHub-Api-Version: 2022-11-28"

if [ ! -f "$ruleset_file" ]; then
  echo "error: preset '${preset}' not found (available: solo, team)" >&2
  exit 1
fi

repo="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
ruleset_name="$(jq -r .name "$ruleset_file")"

existing_id="$(gh api "repos/${repo}/rulesets" \
  --header "$api_version" \
  | jq -r --arg name "$ruleset_name" \
      '.[] | select(.name == $name) | .id // empty' \
  | head -1)"

if [ -n "$existing_id" ]; then
  gh api -X PUT "repos/${repo}/rulesets/${existing_id}" \
    --header "$api_version" \
    --input "$ruleset_file" > /dev/null
  echo "Updated rules '${preset}' (id: ${existing_id}) on ${repo}"
else
  gh api -X POST "repos/${repo}/rulesets" \
    --header "$api_version" \
    --input "$ruleset_file" > /dev/null
  echo "Created rules '${preset}' on ${repo}"
fi

echo "${preset}" > "$preset_file"
echo "Saved preset to .github/rules-preset"
```

### base flake.nix への追加

devShell の packages に `pkgs.gh` と `pkgs.jq` を追加します。

### Profile への組み込み

`small-cli` / `small-web-api` / `small-library` の `parts` に `"features/github-rulesets"` を追加します。Part が全 Profile に入るため、just レシピは base justfile に直接記述できます。

### 依存方向

```text
features/github-rulesets
  └── requires: base
```

`features/ai-agent` / `features/logging` とは独立しており、競合しません。

## 5. 失敗とロールバック

| ケース | 影響 | 対応 |
| --- | --- | --- |
| `gh` 未認証 | `github-setup-rules` が認証エラーで終了 | auth チェックで事前検出し案内メッセージを表示 |
| GitHub リモート未設定 | `github-rules-status` がエラーになる | `gh repo view` チェックで事前検出し exit 0 で案内 |
| `origin` 設定済みで `github-init` 実行 | エラーで停止 | `git push -u origin main && just github-setup` を案内 |
| `Verify` と異なる CI job 名 | status check が機能しない | README に「CI job 名を合わせること」と注記 |
| GitHub API の仕様変更 | JSON が rejected される | `X-GitHub-Api-Version: 2022-11-28` ピン留めで保護。サポート終了告知時に更新 |
| 同名ルールセットが複数存在 | PUT が意図しない ID を更新 | `head -1` で先頭IDのみ取得し、運用は重複を作らない前提とする |

## 6. 検証

| 層 | 検証内容 |
| --- | --- |
| `tests/unit/test_payload.py` | `dot-github/rulesets/solo.json`・`team.json` が payload に存在する |
| `tests/unit/test_payload.py` | `dot-github/rules-preset` が payload に存在する |
| `tests/unit/test_payload.py` | `scripts/github-setup-rules` が payload に存在し実行権限を持つ |
| `tests/unit/test_payload.py` | `solo.json` / `team.json` が valid JSON で `name`・`rules`・`enforcement: "active"` を持つ |
| `tests/e2e/test_generate_profiles.py` | `small-cli` 生成時に `.github/rulesets/solo.json` が出力される |
| `tests/e2e/test_generate_profiles.py` | `small-cli` 生成時に `.github/rules-preset` が出力される |
| `tests/e2e/test_generate_profiles.py` | `small-cli` 生成時に `scripts/github-setup-rules` が出力され実行権限を持つ |
| `tests/e2e/test_generate_profiles.py` | justfile に `github-init` / `github-setup` 等のレシピが存在する |

## 7. 未解決事項

| 項目 | 方針 |
| --- | --- |
| `github-setup-labels` | `github-setup` / `github-status` への1行追加で対応できる設計。将来 Issue |
| `github-setup-repo` | squash merge 設定等。将来 Issue |
| CI job 名のハードコード | `{{ci_check_name}}` 変数は将来 Issue で対応 |
| Organization リポジトリ対応 | `gh api user --jq .login` は個人アカウント専用。別 Issue |
| `bypass_actors` の設定 | チーム運用で必要になったら `team.json` に追加 |
