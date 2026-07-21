管理責任: 設計提案・マイルストーン文書のレビュー(要件対応・責任一意性・失敗定義・
テスト方針・未解決事項)を行います。
ワークフロー: review
状態確認先: `tmp/{work-dir}/design-review.md`

権限: `tmp-write`
副作用: `tmp/{work-dir}/design-review.md`の作成・上書き
承認: 不要です。

設計提案・マイルストーン文書をレビューします。担当Role: Reviewer(subagentへ委譲)。

## 読み込む文書

1. 対象設計文書(`docs/milestones/m{N}-*.md`または設計提案)を読みます
2. `docs/decisions/README.md`一覧で関連する既存判断を確認します
3. `docs/draft/project-direction.md`との整合を確認します

## 手順

1. 利用可能なsubagent機構でsubagent(権限: read-only / tmp-write)へ委譲します。prefix: `design`
2. 詳細な評価軸は[`agent-workflow/skills/design-review/SKILL.md`](../../skills/design-review/SKILL.md)
   を参照します
3. `docs/decisions/`の既存判断と矛盾しないか照合します(矛盾はCritical)
4. Critical/High/Medium/Lowに分類して`tmp/{work-dir}/design-review.md`へ記録します

---

次のステップ:

1. 承認: `/build:test`
2. 要修正: `/plan:design`で再設計
