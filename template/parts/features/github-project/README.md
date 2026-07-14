# features/github-project

## 1. 概要

GitHub プロジェクト管理に必要なテンプレートファイル一式を生成プロジェクトに追加する Part です。全 Profile（`small-cli` / `small-web-api` / `small-library`）に自動的に組み込まれます。

## 2. 責任

- 生成するもの:
  - `.github/PULL_REQUEST_TEMPLATE.md` — PR テンプレート
  - `.github/ISSUE_TEMPLATE/config.yml` — Issue テンプレート設定
  - `.github/ISSUE_TEMPLATE/bug_report.yml` — バグ報告テンプレート
  - `.github/ISSUE_TEMPLATE/feature_request.yml` — 機能追加テンプレート
  - `.github/ISSUE_TEMPLATE/task.yml` — 汎用タスクテンプレート
  - `.github/workflows/ci.yml` — CI ワークフロー（`just verify` を実行）
  - `.github/workflows/update-flake.yml` — `nix flake update` 定期実行ワークフロー
  - `.github/dependabot.yml` — GitHub Actions の依存更新設定
  - `.github/CODEOWNERS` — レビュアー自動アサインのひな型（全行コメントアウト済み）

## 3. 責任外

- GitHub Rulesets / Branch Protection の管理（`features/github-rulesets` が担当）
- Organization リポジトリ固有の設定
- 言語固有の依存更新（dependabot の `package-ecosystem` 設定を直接編集してください）
