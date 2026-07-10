# tests/unit

## 1. 概要

`scripts/`配下のスクリプトや開発環境の宣言(devShell/justfile/pre-commit)を対象にした、依存の少ない自動テストを置くディレクトリです。`just test`で`bats --recursive tests/unit`として実行されます。

## 2. 責任

- 保持するもの: bats形式のユニットテスト。単一スクリプトに対応するテストは`scripts/`配下にミラーし(`scripts/precommit.bats`、`scripts/check-readme.bats`)、複数ファイル間の整合性を検証するテストは`consistency/`配下に置く(`consistency/devshell.bats`)

## 3. 責任外

- 外部プロセスへの実際のネットワークアクセスや、生成先プロジェクトに対する結合テスト(`tests/integration/`が持ちます)
