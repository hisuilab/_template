管理責任: commit・push・PR作成の前に、出荷可能性を判定します。判定結果のみを記録し、
実際のcommit/push/PRは行いません。
ワークフロー: ship(判定)
状態確認先: `tmp/{work-dir}/ship-readiness.md`

権限: `tmp-write`
副作用: `tmp/{work-dir}/ship-readiness.md`の作成・上書き
承認: 不要です。

`../../agent-workflow/commands/ship/readiness.md`を読み、その指示に従ってください。
