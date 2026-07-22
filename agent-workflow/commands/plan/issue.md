管理責任: Issue登録・作業branch・worktree・中央レジストリを確定し、workerへ引き渡します。
ワークフロー: plan(Issue開始)
状態確認先: `tmp/worktrees.json`、Issue worktreeの`tmp/issue-{N}/phase-state.json`

権限: `external-write`(新規GitHub Issue作成)
副作用: GitHub Issue、Issue branch/worktree、phase-state、レジストリの作成
承認: Issue内容・branch・worktree path・外部操作を提示し、承認後に作成します

Production ModeのIssue作業worktreeを確定します。担当Role: Manager→Programmer。

> [!NOTE]
> Prototype ModeではIssue branchとIssue worktreeを使用しません。

## 前提条件

- Production Modeのprimary manager worktreeで`main` branch上にいること
- 対象の設計・要件が確定していること
- local `main`が`origin/main`と同期していること

## 読み込む文書

1. [`naming-policy.md 3.`](../../rules/naming-policy.md#3-ファイルとディレクトリ名)
2. [`workflows.md 4.1.`](../../rules/workflows.md#41-並列worktree状態)
3. [`roles.md 7.`](../../rules/roles.md#7-並列worktreeでの既定配置)
4. `tmp/worktrees.json`(無ければversion 1の空レジストリとして扱います)

## 手順

1. 引数からIssue番号またはタイトルを取得します
2. 既存Issueは`gh issue view N`で内容を確認します。新規Issueは命名規則に沿う日本語の
   title/bodyを作成します
3. [`think:investigate`](../think/investigate.md)に従って事実確認します。Criticalな反証
   (指摘箇所が既修正・Issue重複等)があれば作成前にPMへ確認します
4. 新規Issueの場合はtitle/bodyとGitHubへの外部操作を先に提示して承認を得てから作成し、Issue番号を
   確定します。既存Issueは変更しません。Issue作成に失敗した場合はworktree計画へ進みません
5. 確定したIssue番号から`type/issue-N-topic` branch、`<repository>-issue-{N}`の絶対path、
   担当toolを決めます
6. `scripts/worktree-safety plan-create --manager-root <root> --issue <N> --branch <branch>
   --path <path> --tool <tool>`を実行します。helperが未知version、Issue・branch・pathの競合、
   未登録を含む同時Issue worktree数3への到達を検出した場合は停止します
7. helperが返した作成計画JSONのIssue、branch、絶対path、base SHA、担当tool、現在のworktree数を
   意思決定レポートで提示し、local Git操作の承認を得ます
8. planと同じ入力へ`--approved-base <base_sha>`を付け、`scripts/worktree-safety apply-create`を
   実行します。helper自身がlockを取得し、base・競合・上限・schemaを再検証してからworktree、
   `phase-state.json`、registry entryを作成します
9. helperが状態変化を検出した場合は承認を再利用せず停止します。primary manager worktreeの
   branchは切り替えません。返却JSONと作成結果を報告します
10. Issue作成後にapplyが失敗してもIssueを自動closeしません。部分的に作成されたworktree等を
    自動削除せず、実在状態と再開手順を報告します

---

次のステップ:

1. Issue worktreeで`/auto:issue` — 全フェーズを自動実行
2. Issue worktreeで`/plan:design` — 実装設計から始める
