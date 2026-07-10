# .github

## 1. 概要

GitHubリポジトリの運用設定(Issue/PRテンプレート、CIワークフロー、レビュー担当、依存更新設定)を置くディレクトリです。GitHubがディレクトリ名・ファイル名を規約として認識し、リポジトリの挙動に反映します。

## 2. 責任

- 保持するもの: Issue/PRテンプレート(`ISSUE_TEMPLATE/` `PULL_REQUEST_TEMPLATE.md`)、CIワークフロー(`workflows/`)、レビュー担当割り当て(`CODEOWNERS`)、依存更新設定(`dependabot.yml`)

## 3. 責任外

- リポジトリ本体の開発環境設定(`flake.nix` `treefmt.nix` `.pre-commit-config.yaml`等はリポジトリ直下が持ちます)
