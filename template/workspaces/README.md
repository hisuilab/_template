# template/workspaces

## 1. 概要

`init-workspace` サブコマンドが使用するワークスペーステンプレートを置くディレクトリです。Parts システムとは独立した固定テンプレートです。

## 2. 責任

- ワークスペーステンプレート群（`{name}/` ディレクトリ単位）
- 各テンプレートの `flake.nix`・`dot-envrc`・`justfile`

## 3. 責任外

- Parts システム（`template/parts/` が持ちます）
- ワークスペース生成ロジック（`tooling/generator/workspace.py` が持ちます）
