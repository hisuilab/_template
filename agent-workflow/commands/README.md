# agent-workflow/commands

## 1. 概要

フェーズ別の実行契約(読む文書・権限・副作用・次フェーズ)を、harness非依存の記述として置くディレクトリです。`status.md`・`verify.md`はフェーズに紐付かない横断コマンドです。

## 2. 責任

- `status.md`: 進捗確認コマンドの実行契約
- `verify.md`: 検証コマンドの実行契約
- `manage.md`: primary manager worktreeから行うIssue triage、並列worktreeの状態同期とcleanup
- `think/`・`plan/`・`build/`・`review/`・`ship/`・`verify/`・`auto/`・`template/`: フェーズ別サブディレクトリ(詳細は各READMEを参照)

## 3. 責任外

- Claude Code固有のスラッシュコマンド起動構文(`.claude/commands/`が持ちます)
- Codex固有の呼び出し方法(`.codex/`が持ちます)
