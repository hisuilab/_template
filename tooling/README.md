# tooling

## 1. 概要

新規プロジェクトを生成するジェネレータ本体を置くディレクトリです。`nix run github:hisuilab/_template -- generate --name <name> --profile <profile> --lang <lang> --output <path>` の形でどこからでも呼び出せます。ローカルでは `nix run .# -- generate ...` でも実行可能です。

## 2. 責任

- `generator/`: `template/` の Profile を読み込み、loader / resolver / planner / renderer / applier のパイプラインでプロジェクト一式を生成する Python パッケージ

## 3. 責任外

- Profile・Part の内容（`template/` が持ちます）
