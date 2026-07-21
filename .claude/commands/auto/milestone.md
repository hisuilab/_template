管理責任: 1つのマイルストーンを設計から出荷までフェーズ連鎖で自動的に進めます。
承認ゲートごとに一時停止し、`phase-state.json`を都度更新します。
ワークフロー: think〜shipの全フェーズを横断します
状態確認先: `tmp/milestone-{N}/phase-state.json`

権限: `git-commit`(Prototype Mode) / `external-write`(Production Mode)
副作用: 連鎖するフェーズの全副作用(設計文書更新・テスト・実装・文書同期+commit・レビュー・出荷)
承認: 各フェーズの元コマンドの承認ルールに従います(`/plan:design`のcommit実行直前、
`/build:docs`の複数commit一括提示直前、`/ship:pr`のmerge/push前)。加えて開始時に
対象マイルストーンと開始位置を意思決定レポートで確認します。

`../../agent-workflow/commands/auto/milestone.md`を読み、その指示に従ってください。
