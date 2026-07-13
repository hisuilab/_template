# features/github-rulesets

## 1. 概要

GitHub Rulesets の設定テンプレートと適用スクリプトを生成プロジェクトに追加する Part です。

## 2. 責任

- 生成するもの: `.github/rulesets/solo.json`（個人開発向け）、`.github/rulesets/team.json`（チーム向け）、`scripts/setup-github`（適用スクリプト）
- `scripts/setup-github <preset>` を実行すると、指定プリセットのルールセットを対象リポジトリに適用または更新します（冪等）

## 3. 責任外

- GitHub Actions ワークフローや他の `.github/` ファイルの管理
- `just` レシピへの組み込み（append 戦略実装後に対応予定）
- `Verify` 以外の CI job 名への対応（`solo.json` / `team.json` を直接編集してください）
