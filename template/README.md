# template

## 1. 概要

`tooling/` のジェネレータが読み込む Profile（生成元となるテンプレート一式）を置くディレクトリです。代表3プロファイル（`starter-cli` / `starter-web-api` / `starter-library`）の Part payload が実装済みです。

## 2. 責任

- `schema/`: ProfileSchema / PartSchema の定義・検証（Python パッケージ）
- `profiles/`: プロファイル宣言（`*.toml`）
- `parts/`: Part ごとの `part.toml` と `payload/` テンプレートファイル群
- `workspaces/`: `init-workspace` が使用するワークスペーステンプレート群（Parts システムとは独立した固定テンプレート）

## 3. 責任外

- 生成ロジック本体(`tooling/`が持ちます)
