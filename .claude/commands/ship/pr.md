管理責任: Rigor Modeに応じて出荷を実行します。Prototype Modeは(`/build:docs`が既に
commit済みのmilestoneブランチを)`prototype`へfast-forward merge、Production
Modeはcommit・push・PR作成です。
ワークフロー: ship(実行)
状態確認先: `tmp/{work-dir}/phase-state.json`の`ship`

権限: `git-commit`(Prototype Mode) / `external-write`(Production Mode)
副作用: `prototype`へのfast-forward merge(Prototype Mode)、commit・push・PR作成
(Production Mode)
承認: mergeまたはcommitの実行直前に対象commit一覧を提示します。push・PR作成
(Production Mode)は実行直前に明示承認を得ます。

`../../agent-workflow/commands/ship/pr.md`を読み、その指示に従ってください。
