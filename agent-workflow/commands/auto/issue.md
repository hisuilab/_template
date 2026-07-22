管理責任: 1つのIssueを設計から出荷までフェーズ連鎖で自動的に進めます。
承認ゲートごとに一時停止し、`phase-state.json`を都度更新します。
ワークフロー: think〜shipの全フェーズを横断します
状態確認先: `tmp/issue-{N}/phase-state.json`

権限: `git-commit`(Prototype Mode) / `external-write`(Production Mode)
副作用: 連鎖するフェーズの全副作用(設計文書更新・テスト・実装・文書同期+commit・レビュー・出荷)
承認: 各フェーズの元コマンドの承認ルールに従います(`/plan:design`のcommit実行直前、
`/build:docs`の複数commit一括提示直前、`/ship:pr`のmerge/push前)。加えて開始時に
対象Issueと開始位置を意思決定レポートで確認します。

Issue(単一の実装可能な変更)を全フェーズ自動実行します。担当Role: Programmer(Managerの承認を挟みます)。

## 前提条件

`type/issue-N-topic` ブランチ上で実行してください。それ以外のブランチでは
`/plan:issue N` でブランチを作成するよう案内して終了します。

## 読み込む文書

1. [`workflows.md 1.`](../../rules/workflows.md#1-作業単位とmode検出)でIssue番号/Rigor Modeを
   検出します
2. `tmp/issue-{N}/phase-state.json`で現在フェーズを確認します(ファイルが無い場合は
   空状態として扱います)
3. [`workflows.md 2.`](../../rules/workflows.md#2-フェーズとコマンド)でフェーズ⇔コマンド
   対応を確認します
4. [`workflows.md 5.`](../../rules/workflows.md#5-handoff契約)でHandoff完了条件を確認します

## 手順

1. ブランチ名からIssue番号を検出します
   - `type/issue-N-topic` → N を取得、`tmp/issue-{N}/` を作業ディレクトリとする
   - 上記以外 → `/plan:issue N` でブランチを先に作成するよう案内して終了
2. `phase-state.json`から現在フェーズを検出し、状態レポートと開始位置を意思決定レポートで
   提示します

   ```text
   📋 意思決定 — [auto:issue: 開始位置]

   issue-12 / 進行中フェーズ: implement / 完了: design, test

   1. 進行中のimplementを続ける ← 推奨
   2. designからやり直す(/plan:design)

   どれにしますか?
   ```

3. 選択された開始位置から未完了フェーズを順に実行します(各コマンドの規約に従います)

   ```text
   investigate(/think:investigate N。Criticalな反証があれば停止してPMへ確認)
     → design(/plan:design → design分commitの承認ゲート)
     → test(/build:test、commitしない)
     → implement(/build:implement、commitしない)
     → docs(/build:docs。残りの未commit差分をtest→feat→docsへ分割し、まとめて1回の
       承認ゲート。`build/docs.md`の次のステップの分岐に従います)
     → verify(/verify)
     → review(/review:code、上限3回)
     → ship(/ship:readiness → /ship:pr。push/PR前に承認ゲート)
   ```

   > [!NOTE]
   > `completed`に`investigate`がない既存の`phase-state.json`は「investigate未実施」として
   > 扱い、スキップして`design`から継続します(後方互換)。

4. 承認ゲート(`/plan:design`のcommit直前、`/build:docs`の複数commit一括提示直前、
   `/ship:pr`のpush/PR直前)では意思決定レポートを送り、応答を待ちます
5. 各フェーズ完了時に`phase-state.json`を更新します(中断してもここから再開できます)
6. 完了時に、実行した検証・commit一覧・PR URL・残存事項を報告します

## 停止条件

- 承認ゲートでの否認・方針変更の指示
- ループガードレールの定量上限
  ([`workflows.md 7.`](../../rules/workflows.md#7-ループガードレール))への到達
- 設計判断・依存追加が必要になった時点(PMへ委譲)
- 同じ失敗の繰り返しを検出した場合(ループを止めて原因を報告します)

---

次のステップ:

1. `/status` — 現在地の確認(中断からの再開もここから)
