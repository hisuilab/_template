# scripts

## 1. 概要

開発環境で使う補助スクリプトを置くディレクトリです。`justfile`のrecipeから呼び出され、単体で直接実行することも想定しています。

## 2. 責任

- 保持するもの: `precommit`(gitで追跡されているファイルに対して`prek run`を実行するエントリーポイント)、`check-readme`(ディレクトリごとのREADME.md必須チェック)、`check-status`(`docs/draft`・`docs/milestones`・`docs/decisions`配下のYAML frontmatter `status`値の検証)
- 対応テスト: `tests/unit/scripts/precommit.bats`、`tests/unit/scripts/check-readme.bats`、`tests/unit/scripts/check-status.bats`

## 3. 責任外

- フォーマッタ・linter本体のロジック(treefmt/rumdl/gitleaks/prekが個別に持ちます)
