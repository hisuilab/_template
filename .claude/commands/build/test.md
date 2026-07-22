管理責任: 実装前にテストを作成し、意図した理由でREDになることを確認します。
ワークフロー: build(test) → run(red)
状態確認先: `tmp/{work-dir}/phase-state.json`の`test`

権限: `source-write`
副作用: テストコード作成、`tmp/{work-dir}/`更新
承認: 不要です(マイルストーン/Issue・設計の範囲内で自走します)。

`../../../agent-workflow/commands/build/test.md`を読み、その指示に従ってください。
