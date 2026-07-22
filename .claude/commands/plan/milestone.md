管理責任: マイルストーンの作業ブランチを確定し、実装フェーズへ引き渡せる状態を作ります。
ワークフロー: plan(マイルストーン開始)
状態確認先: `tmp/milestone-{N}/phase-state.json`

権限: `git-commit`
副作用: `m{N}-slug` ブランチの作成、`tmp/milestone-{N}/phase-state.json` の初期化
承認: ブランチ名を提示し、承認後に作成します

`../../../agent-workflow/commands/plan/milestone.md`を読み、その指示に従ってください。
