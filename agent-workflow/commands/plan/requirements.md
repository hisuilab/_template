管理責任: `docs/draft/project-direction.md`(将来`docs/REQUIREMENTS.md`)の位置づけ・
Why/Who/What/Where/When(1〜6節)・未解決の論点(9節)を更新します。実装詳細は含めません。
ワークフロー: plan(要件定義)
状態確認先: `docs/draft/project-direction.md`自身のfrontmatter(`status`。
[`naming-policy.md 4.`](../../rules/naming-policy.md#4-文書の状態管理))

権限: `git-commit`
副作用: `docs/draft/project-direction.md`(または移行後の`docs/REQUIREMENTS.md`)の更新、
その差分のcommit
承認: commit実行直前に差分とcommit messageを提示します。文書更新自体は不要です
(対象範囲内で自走します)。

要件を定義・更新します。担当Role: Architect。

## 読み込む文書

1. `docs/draft/README.md`(概要/責任/責任外)で対象文書の位置づけを確認します
2. `docs/draft/project-direction.md`(frontmatterの`status`が`migrated`の場合は
   `migrated_to`が指す移行先文書)を読みます
3. `docs/decisions/README.md`一覧で関連する過去判断を確認します
4. 新規にdraft文書を作成する場合は
   [`tmp/docs/_template/draft/draft.md`](../../../tmp/docs/_template/draft/draft.md)を
   下敷きにします

## 手順

1. 変更の背景と対象(利用者・価値・範囲・機能・品質のどこか)を特定します
2. 仕様の解釈が分かれる場合は、意思決定レポートでPMへ確認します
3. 対象文書を更新します
   - 実装詳細を要件へ書きません(実現方式は`/plan:architecture`が担当します)
   - 成功条件は検証可能な形で書きます
4. `just verify`でリンク・目次整合を含む検証を確認します
5. 差分とcommit message案(`docs(draft): <変更内容>`形式+`Role:`トレーラー)を提示し、
   承認後にcommitします。差分が無い場合はその旨を報告して終了します
6. 変更の要約と、影響を受けるアーキテクチャ・マイルストーン文書を報告し、フェーズ完了の
   承認を得ます

---

次のステップ:

1. `/plan:architecture` — 実現方式への反映
2. `/plan:design` — マイルストーン/Issueへの分解
