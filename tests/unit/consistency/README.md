# tests/unit/consistency

## 1. 概要

単一のスクリプトではなく、複数ファイルにまたがる宣言の整合性(例: devShellの宣言とjustfile/scriptsが要求するツールの一致)を検証するテストを置くディレクトリです。

## 2. 責任

- 保持するもの: 複数ファイル間の整合性を検証するbatsテスト(`devshell.bats`、`git-hooks.bats`)

## 3. 責任外

- 単一スクリプトの単体挙動(`tests/unit/scripts/`が持ちます)
