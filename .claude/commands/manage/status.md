管理責任: primary manager worktreeから並列Issue worktreeの状態を観測・同期します。
ワークフロー: 横断(全フェーズから参照可能)
状態確認先: `tmp/worktrees.json`、各worktreeの`tmp/issue-{N}/phase-state.json`

権限: `tmp-write`
副作用: `tmp/worktrees.json`の観測値・`updated_at`更新
承認: 不要です。

`../../../agent-workflow/commands/manage.md`を読み、`2. manage:status`の指示に従ってください。
