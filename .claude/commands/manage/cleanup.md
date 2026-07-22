管理責任: primary manager worktreeからマージ済みIssue worktreeの削除を管理します。
ワークフロー: 横断(全フェーズから参照可能)
状態確認先: `tmp/worktrees.json`、各worktreeの`tmp/issue-{N}/phase-state.json`

権限: `git-commit`
副作用: 承認済みworktree・local branchの削除、`tmp/worktrees.json`のregistry更新
承認: 削除計画を提示し、apply実行直前に承認を得ます。

`../../../agent-workflow/commands/manage.md`を読み、`5. manage:cleanup`の指示に従ってください。
