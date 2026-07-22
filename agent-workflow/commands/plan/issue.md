管理責任: IssueのGitHub Issue登録と作業ブランチを確定し、実装フェーズへ引き渡せる状態を作ります。
ワークフロー: plan(Issue開始)
状態確認先: `tmp/issue-{N}/phase-state.json`

権限: `external-write`(GitHub Issue作成)
副作用: GitHub Issue作成、`type/issue-N-topic` ブランチの作成、`tmp/issue-{N}/phase-state.json` の初期化
承認: Issue内容・ブランチ名を提示し、承認後に作成します

Production ModeのIssue作業ブランチを確定します。担当Role: Programmer。

> [!NOTE]
> Prototype Modeでは issue ブランチは使用しません。Production Mode移行後に詳細を実装します。

## 前提条件

- Production Mode(`main` ブランチまたは `type/issue-N-topic` ブランチ上)であること
- 対象の設計・要件が確定していること

## 手順(設計のみ、未実装)

1. 引数からIssue番号またはタイトルを取得します
2. `gh issue view N` で内容を確認します(既存Issueの場合)
3. [`think:investigate`](../think/investigate.md)の手順に従い、事実確認を実施します
   - Criticalな反証(指摘箇所が既修正・Issue重複等)がある場合はブランチ作成前にPMへ確認します
4. ブランチ名 `type/issue-N-topic` を意思決定レポートで提示し、承認を得ます
5. `git checkout -b type/issue-N-topic` を実行します
6. `tmp/issue-{N}/phase-state.json` を初期化します

   ```json
   {
     "completed": [],
     "skipped": [],
     "skip_reasons": {},
     "current": null
   }
   ```

---

次のステップ:

1. `/auto:issue` — 全フェーズを自動実行
2. `/plan:design` — 実装設計から始める
