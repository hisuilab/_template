# docs/decisions

## 1. 概要

このリポジトリで行った設計上の意思決定を記録するディレクトリです。

## 2. 責任

- 保持するもの: 判断の背景・選択肢・採用理由を記録した Decision Record（`YYYY-MM-DD-slug.md`）

## 3. 責任外

- 実装の詳細・マイルストーンの進捗（それぞれ `docs/milestones/` が持ちます）

## 4. 一覧

| 日付 | ファイル | 概要 |
| --- | --- | --- |
| 2026-07-12 | [python-generator](2026-07-12-python-generator.md) | Python 製 generator の採用 |
| 2026-07-13 | [ai-agent-claude-scope](2026-07-13-ai-agent-claude-scope.md) | AI エージェント機能のスコープ判断 |
| 2026-07-13 | [workspace-init-subcommand](2026-07-13-workspace-init-subcommand.md) | workspace init サブコマンドの設計 |
| 2026-07-13 | [workspace-justfile-repo-reference](2026-07-13-workspace-justfile-repo-reference.md) | justfile でのリポジトリ参照方式 |
| 2026-07-13 | [justfile-parameter-vs-placeholder-escape](2026-07-13-justfile-parameter-vs-placeholder-escape.md) | just レシピパラメータと generator プレースホルダーの衝突回避 |
| 2026-07-13 | [ai-agent-unconditional-inclusion](2026-07-13-ai-agent-unconditional-inclusion.md) | features/ai-agent を全プロファイルに無条件同梱する |
| 2026-07-15 | [git-hooks-nix-migration](2026-07-15-git-hooks-nix-migration.md) | pre-commit フック管理を prek から git-hooks.nix へ移行 |
| 2026-07-15 | [nix-in-docker-devcontainer](2026-07-15-nix-in-docker-devcontainer.md) | devcontainer に Nix-in-Docker を採用 |
| 2026-07-21 | [general-purpose-subagent-write-scope](2026-07-21-general-purpose-subagent-write-scope.md) | `general-purpose` subagentへ委譲する際の書き込み範囲の扱い |
