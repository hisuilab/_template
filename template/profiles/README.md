# template/profiles

## 1. 概要

プロジェクト生成に使用するプロファイル宣言（`*.toml`）を置くディレクトリです。各ファイルが使用する Part の組み合わせを定義します。

## 2. 責任

- プロファイルごとの `*.toml` 宣言ファイルの管理

## 3. 責任外

- Part の内容（`template/parts/` が担当）
- プロファイル間の組み合わせルール検証（`tooling/generator/resolver.py` が担当）
