管理責任: 利用可能な検証をすべて実行し、結果と未実行の検証を報告します。何かを修正する
ことはありません。
ワークフロー: run(red)とrun(green)の両方から呼ばれる横断コマンド
状態確認先: `tmp/{work-dir}/phase-state.json`の`verify`

権限: `tmp-write`
副作用: 検証実行と結果レポート(`tmp/`)
承認: 不要です。

`../../agent-workflow/commands/verify.md`を読み、その指示に従ってください。
