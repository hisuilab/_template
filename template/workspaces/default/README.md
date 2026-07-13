# template/workspaces/default

## 1. 概要

`~/Projects` 向けの標準ワークスペーステンプレートです。`just`・`git` を提供する minimal な devShell と、プロジェクト生成用 `new` レシピを含みます。

## 2. 責任

- `flake.nix`: `just`・`git` を含む minimal devShell（nixos-25.11 固定）
- `dot-envrc`: `use flake`（`workspace.py` が `.envrc` として出力）
- `justfile`: `new` レシピ（`nix run github:hisuilab/_template -- generate` を呼ぶ）

## 3. 責任外

- `flake.lock`（`workspace.py` が `nix flake update` を実行して生成します）
- プロジェクトテンプレート（`template/parts/` が持ちます）
