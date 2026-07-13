# features/github-rulesets

## 1. 概要

GitHub Rulesets の設定テンプレートと適用コマンドを生成プロジェクトに追加する Part です。全 Profile（`small-cli` / `small-web-api` / `small-library`）に自動的に組み込まれます。

## 2. 責任

- 生成するもの: `.github/rulesets/solo.json`（個人開発向け）、`.github/rulesets/team.json`（チーム向け）、`.github/rules-preset`（現在のプリセット記録）、`scripts/github-setup-rules`（適用スクリプト）
- base justfile に 5 つの `github-*` レシピを追加します:
  - `github-init [visibility]` — リポジトリ初回作成（非冪等）
  - `github-setup` — 全設定を適用（`.github/rules-preset` 読み取り・冪等）
  - `github-setup-rules [preset]` — Rules を適用・`.github/rules-preset` を更新
  - `github-status` — 全設定の現状を表示
  - `github-rules-status` — 現在 GitHub に適用されている Rules を表示
- base flake.nix の devShell に `pkgs.gh` / `pkgs.jq` を追加します

## 3. 責任外

- GitHub Actions ワークフローや他の `.github/` ファイルの管理
- Organization リポジトリへの対応
- `Verify` 以外の CI job 名への対応（`solo.json` / `team.json` を直接編集してください）
- `github-setup-labels` 等の将来拡張（`github-setup` / `github-status` への1行追加で対応できる設計）
