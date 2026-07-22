管理責任: 秘密情報露出・権限整合・外部公開ゲート・サプライチェーンのレビューを行います。
ワークフロー: review
状態確認先: `tmp/{work-dir}/security-review.md`

権限: `tmp-write`
副作用: `tmp/{work-dir}/security-review.md`の作成・上書き
承認: 不要です。

差分・設定ファイルをセキュリティ観点でレビューします。担当Role: Reviewer(subagentへ委譲)。

## 読み込む文書

1. 対象差分、`.gitleaks.toml`、CI/pre-commit設定(`.pre-commit-config.yaml`)を確認します
2. [`agent-workflow/rules/command-permissions.md`](../../rules/command-permissions.md)を確認します

## 手順

1. 利用可能なsubagent機構でsubagent(権限: read-only / tmp-write)へ委譲します。prefix: `security`
2. 詳細な評価軸は[`agent-workflow/skills/security-review/SKILL.md`](../../skills/security-review/SKILL.md)
   を参照します
3. Critical/High指摘は修正またはPM判断まで出荷を止めます
4. `tmp/{work-dir}/security-review.md`へ記録します

---

次のステップ:

1. 承認: `/ship:readiness`
2. 要修正: 指摘に対応後、再レビュー
