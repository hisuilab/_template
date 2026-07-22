# .claude/commands/manage

## 1. 概要

並列Issue worktreeの観測・担当変更・クリーンアップを行うスラッシュコマンドを置くディレクトリです。

## 2. 責任

- `status.md`: 全worktreeまたは指定worktreeの状態を同期・表示する
- `assign.md`: worktreeの担当ツール(claude/codex/human)を変更する
- `cleanup.md`: マージ済みworktreeの削除計画を作成し、承認後に適用する

## 3. 責任外

- コマンドの実行契約の内容そのもの(`agent-workflow/commands/manage.md`が持ちます)
- worktree作成(`/plan:issue`が担います)
