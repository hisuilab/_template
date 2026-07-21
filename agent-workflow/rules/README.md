# agent-workflow/rules

## 1. 概要

Rigor Mode・フェーズ・Role・Handoff・命名・権限・レビューループ・Audit Gateなど、AIエージェント運用の横断ルールを置くディレクトリです。

## 2. 責任

- `workflows.md`: 作業単位とMode検出、フェーズとコマンドの対応、レビューループプロトコル、Audit Gate
- `roles.md`: Manager/Architect/Programmer/Reviewer/Testerの責務定義
- `naming-policy.md`: Milestone/Issue・commit・branch・作業ファイルの命名規則
- `command-permissions.md`: コマンドの権限レベル・承認ルール・subagent境界
- `policy.md`: 作業開始・変更・Gitと外部操作・完了報告・PM-エンジニアモデルの基本方針

## 3. 責任外

- 特定AIツールでの実行方法(`.claude/commands/`・`.codex/`が持ちます)
