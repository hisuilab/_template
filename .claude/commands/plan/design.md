管理責任: マイルストーン単位の詳細設計(実装計画・完了条件)を作成・更新します。
Production Modeでは対象Issueの設計提案を作成します。
ワークフロー: plan(詳細設計)
状態確認先: `docs/milestones/m{N}-*.md`(Prototype Mode)、Issue本文または`docs/design/`
(Production Mode)

権限: `git-commit`
副作用: マイルストーン文書または設計提案の作成・更新、design分のcommit
承認: commit実行直前に差分とcommit messageを提示します。文書作成自体は不要です
(対象マイルストーン/Issueの範囲内で自走します)。

`../../agent-workflow/commands/plan/design.md`を読み、その指示に従ってください。
