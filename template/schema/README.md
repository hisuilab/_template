# template/schema

## 1. 概要

`part.toml` と `profile.toml` の構造を検証し、不変データクラスとして返す Python パッケージです。

## 2. 責任

- `ProfileSchema` / `PartSchema` の定義と `validate_*` 関数による検証
- 検証エラーを `SchemaError`（`errors.py`）として報告

## 3. 責任外

- プロジェクト生成ロジック（`tooling/generator/` が担当）
- `template/parts/` や `template/profiles/` の内容管理
