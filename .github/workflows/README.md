# .github/workflows

## 1. 概要

GitHub Actionsのワークフロー定義を置くディレクトリです。GitHubがこのディレクトリ名を規約として認識し、push・pull_request・スケジュール等のイベントに応じて自動実行します。

## 2. 責任

- 保持するもの: CI(`ci.yml`)、Nix flakeの月次自動更新(`update-flake.yml`)

## 3. 責任外

- CIが呼び出すタスクの実体(`justfile`が正本を持ちます。ここでは個別列挙しません)
