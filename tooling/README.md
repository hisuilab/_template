# tooling

## 1. 概要

新規プロジェクトを生成するジェネレータ本体を置くディレクトリです。`python3 -m tooling.generator generate --name <name> --profile <profile> --output <path>` の形で呼び出します。

## 2. 責任

- `generator/`: `template/` の Profile を読み込み、loader / resolver / planner / renderer / applier のパイプラインでプロジェクト一式を生成する Python パッケージ

## 3. 責任外

- Profile・Part の内容（`template/` が持ちます）
