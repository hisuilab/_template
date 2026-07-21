管理責任: `docs/draft/project-direction.md`のHow(7〜8節)、将来`docs/DESIGN.md`を更新します。
ワークフロー: plan(アーキテクチャ設計)
状態確認先: `docs/draft/project-direction.md`自身のfrontmatter(`status`)

権限: `git-commit`
副作用: `docs/draft/project-direction.md`(または移行後の`docs/DESIGN.md`)の更新、その差分の
commit
承認: commit実行直前に差分とcommit messageを提示します。文書更新自体は不要です
(対象範囲内で自走します)。

内部構造・責務分離・依存方向を設計・更新します。担当Role: Architect。

## 読み込む文書

1. `docs/draft/project-direction.md`(Why/Who/What部分)を読みます
2. 対象ディレクトリ一式のREADME.md(概要/責任/責任外)を読み、現状の責務分離を確認します
3. `docs/decisions/README.md`一覧で既存判断との矛盾がないか確認します
4. 新規にアーキテクチャ文書を作成する場合は、中核サブシステムなら
   [`tmp/docs/_template/architecture/core.md`](../../../tmp/docs/_template/architecture/core.md)、
   バリアント仕様シートなら
   [`spec-sheet.md`](../../../tmp/docs/_template/architecture/spec-sheet.md)を下敷きにします

## 手順

1. 対象範囲の現状構造(ディレクトリ・責務境界・依存方向)を、README.mdを起点に確認します
2. 変更が必要な場合、代替案を比較し、選択理由とトレードオフを明示します
3. 対象文書を更新します(現行実装と未実装の目標設計を混同せず、目標設計には明示ラベルを付けます)
4. 既存判断と矛盾する場合は`docs/decisions/`へ新しいDecision Recordを作成します
   (**実装前**に判明した設計判断が対象です。実装中に初めて発覚した判断は`/build:docs`が
   担当します)
5. `just verify`で整合を確認します
6. 差分とcommit message案(`docs(draft): <変更内容>`形式+`Role:`トレーラー)を提示し、
   承認後にcommitします。差分が無い場合はその旨を報告して終了します

---

次のステップ:

1. `/plan:design` — マイルストーン/Issue単位の詳細設計
2. `/review:design` — 設計レビュー
