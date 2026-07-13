# .github/rulesets

## 1. 概要

GitHub Rulesets の設定テンプレートを格納するディレクトリです。`scripts/github-setup-rules` を実行すると、指定のプリセットをリポジトリに適用または更新します。

## 2. 責任

- `solo.json` — 個人開発向けルールセット（PR 必須・CI 必須・force push 禁止）
- `team.json` — チーム開発向けルールセット（承認1件必須・stale review 無効化を追加）

## 3. 責任外

- ルールセットの GitHub への適用（`scripts/github-setup-rules` が担当）
- `solo.json` / `team.json` 以外のプリセット
