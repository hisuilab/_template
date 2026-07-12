# tests/unit

## 1. 概要

`scripts/`、`template/` 等を対象にした依存の少ない自動テストを置くディレクトリです。`just test` で bats と pytest の両方を実行します。

## 2. 責任

- bats テスト: scripts/ に 1:1 対応する `scripts/*.bats`、整合性テスト `consistency/devshell.bats`
- pytest テスト: `test_schema.py`（template/schema 検証）、`test_payload.py`（payload 整合検証）、`test_generator.py`（tooling/generator パイプライン検証）

## 3. 責任外

- 外部プロセスへの実際のネットワークアクセスや、生成先プロジェクトに対する結合テスト(`tests/integration/`が持ちます)
