管理責任: マイルストーン単位の詳細設計(実装計画・完了条件)を作成・更新します。
Production Modeでは対象Issueの設計提案を作成します。
ワークフロー: plan(詳細設計)
状態確認先: `docs/milestones/m{N}-*.md`(Prototype Mode)、Issue本文または`docs/design/`
(Production Mode)

権限: `git-commit`
副作用: マイルストーン文書または設計提案の作成・更新、design分のcommit
承認: commit実行直前に差分とcommit messageを提示します。文書作成自体は不要です
(対象マイルストーン/Issueの範囲内で自走します)。

作業単位の詳細設計(完了条件・実装計画・未解決事項)を作成します。担当Role: Architect。

## 読み込む文書

1. `docs/draft/project-direction.md`(方向性)を読みます
2. `docs/milestones/README.md`で対象マイルストーンの依存関係を確認します
3. 対象範囲のディレクトリ一式のREADME.mdを読みます
4. 直前のマイルストーン文書(あれば)の「前提とする未解決事項」を確認します
5. 新規作成時はPrototype Modeなら
   [`tmp/docs/_template/milestone/milestone.md`](../../../tmp/docs/_template/milestone/milestone.md)、
   Production Modeなら
   [`tmp/docs/_template/design-proposal/design-proposal.md`](../../../tmp/docs/_template/design-proposal/design-proposal.md)を
   下敷きにします

## 手順

1. Prototype Modeでは、目標・完了条件・実装計画を`milestone.md`テンプレートの章構成
   (概要/完了条件/実装計画/前提とする未解決事項)で作成します。Production Modeでは
   `design-proposal.md`テンプレートの章構成で設計提案を作成します
2. 完了条件は検証可能な形で書きます(`nix build`成功、テスト追加等の具体的な条件)
3. 実装計画は依存の浅い層から進める順序で並べます
4. 対象外・先送りにする論点を「前提とする未解決事項」(design-proposalでは「未解決事項」)に
   明記します
5. Prototype Modeでは`docs/milestones/README.md`の一覧表に行を追加します
6. `just verify`で整合を確認します
7. Prototype Modeで新規作成した場合は、`docs/milestones/m{N}-*.md`・
   `docs/milestones/README.md`の差分とcommit message案
   (`docs(milestones): add M{N} <slug> milestone`形式+`Role:`トレーラー)を提示し、
   承認後にcommitします。Production Modeで`docs/design/`へファイルを作成した場合も
   同様です(Issue本文のみの場合、commit対象なしとして終了します)。既にcommit済みで
   差分が無い場合は、その旨を報告して終了します
8. test/implement中に設計判断が必要と分かり([`workflows.md 7.`](../../rules/workflows.md#7-ループガードレール)の
   停止条件に該当し)PMの承認を得た上で本コマンドへ戻ってきた場合は、既存のdesign commit
   を`commit --amend`や`reset`で書き換えず、**追加commit**として扱います。「当初どう
   設計してどこで詰まったか」を`git diff`で追えるようにするためです。commit message案は
   `docs(milestones): revise M{N} <slug> plan`形式とし、修正理由を本文に1〜2行で添えます

---

次のステップ:

1. `/build:test` — テスト先行
2. `/review:design` — 設計レビュー
