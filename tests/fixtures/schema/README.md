# tests/fixtures/schema

## 1. 概要

`template/schema/` のユニットテスト（`tests/unit/test_schema.py`）で使用する TOML フィクスチャファイルを置くディレクトリです。

## 2. 責任

- 正常系・異常系の `part.toml` / `profile.toml` サンプルファイルの管理

## 3. 責任外

- テストコード本体（`tests/unit/test_schema.py` が担当）
- 実際のプロジェクト生成に使うプロファイル（`template/profiles/` が担当）
