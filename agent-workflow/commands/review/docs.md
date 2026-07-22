管理責任: 文書の整合性レビュー(リンク・目次・文体・README構成)を行います。
ワークフロー: review
状態確認先: `tmp/{work-dir}/docs-review.md`

権限: `tmp-write`
副作用: `tmp/{work-dir}/docs-review.md`の作成・上書き
承認: 不要です。

変更された文書をレビューします。担当Role: Reviewer(subagentへ委譲)。

## 読み込む文書

1. 変更された文書一式(`git diff`)を確認します
2. `rumdl.toml`、`scripts/check-readme`の規約を確認します
3. `AGENTS.md`(です・ます調、番号付き目次等の文書規約)を確認します

## 手順

1. 利用可能なsubagent機構でsubagent(権限: read-only / tmp-write)へ委譲します。prefix: `docs`
2. 詳細な評価軸は[`agent-workflow/skills/docs-sync/SKILL.md`](../../skills/docs-sync/SKILL.md)を参照します
3. `just verify`相当(rumdl・check-readme)を実行し、機械的に検出できる指摘と、
   文体・整合性など機械検出できない指摘を分けて記録します
4. Critical/High/Medium/Lowに分類して`tmp/{work-dir}/docs-review.md`へ記録します

---

次のステップ:

1. 承認: `/ship:readiness`
2. 要修正: `/build:docs`
