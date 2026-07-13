---
status: approved
proposed_at: 2026-07-13
approved_at: 2026-07-13
approved_by: PM
approval_ref: "https://github.com/hisuilab/_template/issues/40"
implemented_at: null
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
| `features/github-rulesets` Part の新規追加 | 既存 Profile への自動組み込み |
| `solo.json` / `team.json` ルールセットテンプレート | Branch Protection Rules との併用管理 |
| `scripts/setup-github` 適用スクリプト | GitHub Actions 等の他の `.github/` ファイル |
| 単体テスト・e2e テストの追加 | `just` レシピへの組み込み（append 戦略未実装のため） |

## 3. 選択肢

| # | 選択肢 | 採否 |
| --- | --- | --- |
| A | JSON テンプレート + 適用スクリプトを Part として提供 | 採用 |
| B | `docs/development/` にドキュメントのみ記載 | 不採用（再現性がない） |

## 4. 設計案

### ファイル構成

```text
template/parts/features/github-rulesets/
├── part.toml
├── README.md
└── payload/
    ├── dot-github/
    │   └── rulesets/
    │       ├── solo.json
    │       └── team.json
    └── scripts/
        └── setup-github
```

`dot-github/` プレフィックスは planner.py が除去するため、生成先では `.github/rulesets/` として出力されます。

### `part.toml`

```toml
[part]
id = "features/github-rulesets"
requires = ["base"]
conflicts = []
```

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
        "required_status_checks": [
          { "context": "Verify" }
        ]
      }
    }
  ]
}
```

**`team.json`** — チーム向け。solo の設定に加え、承認1件必須・stale review 無効化。

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
        "required_status_checks": [
          { "context": "Verify" }
        ]
      }
    }
  ]
}
```

### `scripts/setup-github` の設計

- 引数: `solo`（既定）または `team`
- 動作: GET で同名ルールセットを検索 → 存在すれば PUT（更新）、なければ POST（新規作成）
- API バージョン: `X-GitHub-Api-Version: 2022-11-28` をヘッダでピン留め
- 依存: `gh` CLI（認証済み）、`jq`

```sh
#!/usr/bin/env bash
# requires: gh, jq
set -euo pipefail

preset="${1:-solo}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ruleset_file="$script_dir/../.github/rulesets/${preset}.json"

if [ ! -f "$ruleset_file" ]; then
  echo "error: preset '${preset}' not found (available: solo, team)" >&2
  exit 1
fi

repo="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
ruleset_name="$(jq -r .name "$ruleset_file")"
api_version="X-GitHub-Api-Version: 2022-11-28"

existing_id="$(gh api "repos/${repo}/rulesets" \
  --header "$api_version" \
  | jq -r --arg name "$ruleset_name" '.[] | select(.name == $name) | .id // empty')"

if [ -n "$existing_id" ]; then
  gh api -X PUT "repos/${repo}/rulesets/${existing_id}" \
    --header "$api_version" \
    --input "$ruleset_file"
  echo "Updated ruleset '${preset}' (id: ${existing_id}) on ${repo}"
else
  gh api -X POST "repos/${repo}/rulesets" \
    --header "$api_version" \
    --input "$ruleset_file"
  echo "Created ruleset '${preset}' on ${repo}"
fi
```

### 依存方向

```text
features/github-rulesets
  └── requires: base
```

`features/ai-agent` / `features/logging` とは独立しており、競合しません。

## 5. 失敗とロールバック

| ケース | 影響 | 対応 |
| --- | --- | --- |
| `gh` 未認証 | `setup-github` が認証エラーで終了 | `gh auth login` を先に実行するよう README に明記 |
| `Verify` と異なる CI job 名 | status check が機能しない | README に「CI job 名を合わせること」と注記 |
| GitHub API の仕様変更 | JSON が rejected される | `X-GitHub-Api-Version: 2022-11-28` ピン留めで保護。サポート終了告知時に更新 |
| 同名ルールセットが複数存在 | PUT が意図しない ID を更新 | `setup-github` は1件のみ更新し、複数存在時はエラーメッセージを表示 |

## 6. 検証

| 層 | 検証内容 |
| --- | --- |
| `tests/unit/test_payload.py` | `dot-github/rulesets/solo.json`・`team.json` が payload に存在する |
| `tests/unit/test_payload.py` | `scripts/setup-github` が payload に存在し実行権限を持つ |
| `tests/e2e/test_generate_profiles.py` | `features/github-rulesets` を含む Profile を生成すると `.github/rulesets/solo.json` が出力される |

## 7. 未解決事項

- CI job 名 `Verify` は現在ハードコード。将来的には `{{ci_check_name}}` 変数で注入できるようにすることを検討する
- `just setup-github` レシピは append 戦略（M11+）が実装されてから追加する
