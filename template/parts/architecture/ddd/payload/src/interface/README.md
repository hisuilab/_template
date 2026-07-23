# src/interface

## 1. 概要

外部とのインターフェース実装を置くディレクトリです。

## 2. 責任

- API・CLI・Web・バッチジョブなどの入出力アダプターを格納します

## 3. 責任外

- ビジネスロジック（`src/domain/` が担当）
- ユースケース定義（`src/application/` が担当）

<!-- この README は architecture/layered/payload/src/interface/README.md と同一内容です。
     consistency test (tests/unit/test_payload.py::test_mirrored_readmes) で保護されています。
     内容を変更する場合は両方を同時に更新してください。 -->
