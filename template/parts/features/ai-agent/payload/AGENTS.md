# AGENTS

AI エージェント向けの開発ガイドラインです。

## 目次

- [1. リポジトリ探索](#1-リポジトリ探索)
- [2. コミットメッセージ](#2-コミットメッセージ)

## 1. リポジトリ探索

AI agentはリポジトリ探索に次の優先順位で使います。

1. テキスト検索（ripgrep）とファイル読み取りを基本とします
2. LSP serverがdevShellで利用可能な場合、semantic探索（definition・references・
   diagnostics・hover）をテキスト検索の補助として任意に使います
3. MCP serverが設定されている場合、read-only toolを任意のsemantic探索補助として使います。
   write toolの使用はユーザーへの確認なしに行いません
4. LSP/MCPが利用できない場合はテキスト検索にfallbackします（hooksによる強制は行いません）

## 2. コミットメッセージ

- 英語で、[Conventional Commits](https://www.conventionalcommits.org/) 形式（`type(scope): description`）で書きます
- `type` は `build`/`chore`/`ci`/`docs`/`feat`/`fix`/`perf`/`refactor`/`revert`/`style`/`test` のいずれかを使います
