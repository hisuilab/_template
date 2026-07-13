# GitHub リポジトリ設定ガイドライン

## 目次

- [1. 概要](#1-概要)
- [2. Branch Protection Rules](#2-branch-protection-rules)
- [3. CODEOWNERS](#3-codeowners)
- [4. 設定の確認方法](#4-設定の確認方法)
- [5. 設定変更の手順](#5-設定変更の手順)

## 1. 概要

`main` ブランチへの直接 push 禁止・CI 必須・force push 禁止を GitHub 側で強制します。
これにより CI をすり抜けたコードや未レビューの変更が `main` に混入することを防ぎます。

## 2. Branch Protection Rules

`main` ブランチに以下のルールを適用しています。

| 項目 | 設定値 | 理由 |
| --- | --- | --- |
| Required status checks | `Verify`（CI job）パス必須 | `just verify` 相当の検証が通らないとマージ不可 |
| Require PR before merging | 有効 | 直接 push 禁止。すべての変更は PR 経由 |
| Require code owner review | 有効（`CODEOWNERS` 参照） | CODEOWNERS で指定された owner のレビューが必要 |
| Required approving review count | 0 | 単独開発のため承認数は要求しない |
| Dismiss stale reviews | 無効 | push のたびに再承認を要求しない |
| Enforce for admins | 無効 | 管理者は bypass 可（緊急時対応のため） |
| Allow force pushes | 禁止 | `main` の履歴を書き換えない |
| Allow deletions | 禁止 | `main` ブランチを削除しない |

### 設定コマンド（再適用時）

```sh
gh api -X PUT repos/hisuilab/_template/branches/main/protection \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": false,
    "checks": [{ "context": "Verify" }]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": false,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 0
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": false
}
EOF
```

## 3. CODEOWNERS

`.github/CODEOWNERS` で `@hisuilab` をすべてのファイルのデフォルト owner として設定しています。Branch Protection の `require_code_owner_reviews: true` と組み合わせることで、PR 作成時に自動でレビュアーが割り当てられます。

特に慎重なレビューが必要なパスには個別にエントリを設けています（`AGENTS.md`、`CLAUDE.md`、`flake.nix`、`.github/` 等）。

## 4. 設定の確認方法

現在の branch protection 設定を確認するには:

```sh
gh api repos/hisuilab/_template/branches/main/protection | jq '{
  required_status_checks: .required_status_checks.checks,
  require_pr: .required_pull_request_reviews.require_code_owner_reviews,
  allow_force_pushes: .allow_force_pushes.enabled,
  allow_deletions: .allow_deletions.enabled
}'
```

## 5. 設定変更の手順

branch protection の変更はインフラへの永続変更のため、以下のプロセスを踏みます。

1. 変更内容を Issue またはチャットで説明し、PM の明示的な承認を得る
2. 承認後に `gh api` で設定を適用する
3. 本ドキュメントの該当箇所を更新して PR を作成する
