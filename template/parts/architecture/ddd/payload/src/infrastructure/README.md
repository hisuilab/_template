# src/infrastructure

## 1. 概要

外部システムとの接続実装を置くディレクトリです。

## 2. 責任

- データベース・外部 API・メッセージキューなどの実装を格納します

## 3. 責任外

- ビジネスロジック（`src/domain/` が担当）
- ユースケース定義（`src/application/` が担当）

<!-- この README は architecture/layered/payload/src/infrastructure/README.md と同一内容です。
     consistency test (tests/unit/test_payload.py::test_mirrored_readmes) で保護されています。
     内容を変更する場合は両方を同時に更新してください。 -->
