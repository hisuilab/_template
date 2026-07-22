管理責任: リポジトリ全体をRed Team Auditとして横断監査します。マイルストーン完了宣言と
リリース前(Production Mode)に実行します。Prototype Modeでは必須にしません。
ワークフロー: review(Audit Gate)
状態確認先: `tmp/{work-dir}/audit-review.md`または`tmp/audit/YYYY-MM-DD-repository-audit.md`

権限: `tmp-write`
副作用: `tmp/{work-dir}/audit-review.md`または`tmp/audit/YYYY-MM-DD-repository-audit.md`の作成・上書き
承認: 不要です。

`../../../agent-workflow/commands/review/audit.md`を読み、その指示に従ってください。
