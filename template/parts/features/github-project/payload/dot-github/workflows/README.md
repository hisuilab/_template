# .github/workflows

## 1. 概要

GitHub Actions ワークフローを管理するディレクトリです。

## 2. 責任

- CI ワークフロー（`ci.yml`）: `just verify` を実行してコードの整合性を確認します
- Flake 更新ワークフロー（`update-flake.yml`）: 週次で `nix flake update` を実行して PR を作成します

## 3. 責任外

- GitHub Rulesets の設定（`../ rulesets/` が担当）
- Issue / PR テンプレート（`../ISSUE_TEMPLATE/` が担当）
