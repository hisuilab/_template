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
4. `/manage:status`相当でレジストリと`git worktree list --porcelain`を照合します。未知version、
   同じIssue・branch・pathの競合、または同時Issue worktree数3への到達時は作成を停止します
5. `type/issue-N-topic` branchと`<repository>-issue-{N}` pathを決めます。新規Issueの場合は
   Issue作成後に確定する番号を使います
6. Issue内容、branch、絶対path、base commit、実行する外部操作を意思決定レポートで提示し、
   承認を得ます
7. 新規Issueの場合のみGitHub Issueを作成します。既存Issueは変更しません
8. `git worktree add <path> -b <branch> main`でworktreeを作成します。primary manager
   worktree自体のbranchは切り替えません。branchが既に存在する場合は自動再利用せず、既存の
   worktree・PRとの対応を報告して停止します
9. `<path>/tmp/issue-{N}/phase-state.json`を初期化します

   ```json
   {
     "completed": [],
     "skipped": [],
     "skip_reasons": {},
     "current": null
   }
   ```

10. primary manager worktreeの`tmp/worktrees.json`へ`status: active`で登録し、JSONを
    原子的に置換します。担当ツール未定なら`assigned_tool: null`とします
11. Issue作成後にworktree作成が失敗してもIssueを自動closeしません。worktree作成後に
    レジストリ更新が失敗した場合もworktreeを自動削除せず、実在状態と再開手順を報告します

---

次のステップ:

1. Issue worktreeで`/auto:issue` — 全フェーズを自動実行
2. Issue worktreeで`/plan:design` — 実装設計から始める
