# tests

## 1. 概要

テストを層ごとに分けて置くディレクトリです。`just test` は `test-bats`（`bats --recursive tests/unit`）と `test-py`（`pytest`）を順に実行します。

## 2. 責任

- 保持するもの: `unit/`（ユニットテスト）、`integration/`（結合テスト）、`e2e/`（エンドツーエンドテスト）のディレクトリ分割

## 3. 責任外

- 各層のテストコード自体の責任範囲（それぞれの README が持ちます）
