# scripts

## 1. 概要

開発環境で使う補助スクリプトを置くディレクトリです。`justfile` のレシピから呼び出され、単体で直接実行することも想定しています。

## 2. 責任

- `check-readme`: ディレクトリごとの README.md 必須チェック
- `check-status`: `docs/draft`・`docs/milestones`・`docs/decisions` 配下の YAML frontmatter `status` 値の検証
- `check-encoding`: U+FFFD 文字化けの検出

## 3. 責任外

- フォーマッタ・linter 本体のロジック（treefmt / rumdl / gitleaks / prek が個別に持ちます）
