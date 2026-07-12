# tests/e2e

## 1. 概要

`tooling/`のジェネレータで実際にプロジェクトを生成し、生成物に対して check-readme / check-status / check-encoding を実行するエンドツーエンドテストを置くディレクトリです。

## 2. 責任

- 保持するもの: 生成〜bash スクリプト検証までを通しで確認するエンドツーエンドテスト(`test_generate_profiles.py`)

## 3. 責任外

- ジェネレータ本体のユニットテスト(`tooling/`配下が持ちます)
