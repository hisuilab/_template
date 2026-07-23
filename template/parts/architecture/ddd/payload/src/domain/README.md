# src/domain

## 1. 概要

ドメインモデルとビジネスロジックを置くディレクトリです。

## 2. 責任

- エンティティ・値オブジェクト・ドメインサービス・リポジトリインターフェースを格納します

## 3. 責任外

- アプリケーション層のオーケストレーション（`src/application/` が担当）
- インフラストラクチャの実装詳細（`src/infrastructure/` が担当）

<!-- この README は architecture/layered/payload/src/domain/README.md と同一内容です。
     consistency test (tests/unit/test_payload.py::test_mirrored_readmes) で保護されています。
     内容を変更する場合は両方を同時に更新してください。 -->
