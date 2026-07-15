# .devcontainer

## 1. 概要

VS Code devcontainer の設定ファイルを置くディレクトリです。Docker + VS Code のみで Nix 開発環境を再現し、Nix 未経験者や Windows ユーザーが `nix develop` を意識せずに開発できるようにします。

## 2. 責任

- `devcontainer.json`: ベースイメージ・Nix feature・postCreateCommand・VS Code 拡張の構成
- `postCreateCommand` で `nix develop --command` を実行し、devShell の shellHook 経由で git フック（treefmt / rumdl / gitleaks / check-readme / convco）を自動インストールします

## 3. 責任外

- Nix flake・devShell・パッケージの定義（`flake.nix` が担当）
- git フックの実装と管理（`git-hooks.nix` が担当）
