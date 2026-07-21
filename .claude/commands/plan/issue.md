管理責任: IssueのGitHub Issue登録と作業ブランチを確定し、実装フェーズへ引き渡せる状態を作ります。
ワークフロー: plan(Issue開始)
状態確認先: `tmp/issue-{N}/phase-state.json`

権限: `external-write`(GitHub Issue作成)
副作用: GitHub Issue作成、`type/issue-N-topic` ブランチの作成、`tmp/issue-{N}/phase-state.json` の初期化
承認: Issue内容・ブランチ名を提示し、承認後に作成します

`../../agent-workflow/commands/plan/issue.md`を読み、その指示に従ってください。
