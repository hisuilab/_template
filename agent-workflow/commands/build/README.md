# agent-workflow/commands/build

## 1. 概要

テスト先行・実装・文書同期という`build`フェーズの実行契約を置くディレクトリです。

## 2. 責任

- `test.md`: テスト先行(RED確認)の実行契約
- `implement.md`: 実装(GREEN確認)の実行契約
- `docs.md`: 文書同期・commitの実行契約

## 3. 責任外

- テスト・実装コードそのもの(対象リポジトリの`tests/`・`src/`等が持ちます)
