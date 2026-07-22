# agent-workflow

## 1. 概要

AIエージェント運用ワークフロー(Rigor Mode・フェーズ・Role・Handoff・命名・権限・レビューループ・Audit Gate)の、harness非依存な正本を置くディレクトリです。どのAIツール(Claude Code・Codex等)から実行するかに関わらず共通する「決めごと」をここに集約します(Issue #114)。

## 2. 責任

- `rules/`: Rigor Mode・フェーズ・Role・Handoff・命名・権限などの横断ルール
- `commands/`: フェーズ別の実行契約(読む文書・権限・副作用・次フェーズ)のharness非依存な記述
- `agents/`: Role(Architect/Programmer/Reviewer/Tester)の役割・評価軸の本文
- `skills/`: レビュー・docs同期・handoff確認の詳細手順本文

## 3. 責任外

- 特定AIツールの実行機構(スラッシュコマンドの起動構文・subagentのツール制限・Skillの自動発火条件・hookイベント)は`.claude/`・`.codex/`が持ちます
- `agent-workflow/agents/`はRoleの役割記述であり、Claude Code固有のsubagent定義(`tools:`/`model:`フィールド)を持つ`.claude/agents/`とは別物です
