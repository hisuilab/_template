管理責任: 1つのマイルストーンを設計から出荷までフェーズ連鎖で自動的に進めます。
承認ゲートごとに一時停止し、`phase-state.json`を都度更新します。
ワークフロー: think〜shipの全フェーズを横断します
状態確認先: `tmp/milestone-{N}/phase-state.json`

権限: `git-commit`(Prototype Mode) / `external-write`(Production Mode)
副作用: 連鎖するフェーズの全副作用(設計文書更新・テスト・実装・文書同期+commit・レビュー・出荷)
承認: 各フェーズの元コマンドの承認ルールに従います(`/plan:design`のcommit実行直前、
`/build:docs`の複数commit一括提示直前、`/ship:pr`のmerge/push前)。加えて開始時に
対象マイルストーンと開始位置を意思決定レポートで確認します。

マイルストーン(大きな目標・機能単位)を全フェーズ自動実行します。担当Role: Programmer(Managerの承認を挟みます)。

## 前提条件

`m{N}-slug` ブランチ上で実行してください。`prototype` または `main` ブランチ上で実行した
場合は `/plan:milestone N` でブランチを作成するよう案内して終了します。

## 読み込む文書

1. [`workflows.md 1.`](../../rules/workflows.md#1-作業単位とmode検出)でマイルストーンID/Rigor Modeを
   検出します
2. `tmp/milestone-{N}/phase-state.json`で現在フェーズを確認します(ファイルが無い場合は
   空状態として扱います)
3. [`workflows.md 2.`](../../rules/workflows.md#2-フェーズとコマンド)でフェーズ⇔コマンド
   対応を確認します
4. [`workflows.md 5.`](../../rules/workflows.md#5-handoff契約)でHandoff完了条件を確認します

## 手順

1. ブランチ名からマイルストーションIDを検出します
   - `m{N}-slug` → N を取得、`tmp/milestone-{N}/` を作業ディレクトリとする
   - `prototype` または上記以外 → `/plan:milestone N` でブランチを先に作成するよう案内して終了
2. `phase-state.json`から現在フェーズを検出し、状態レポートと開始位置を意思決定レポートで
   提示します

   ```text
   📋 意思決定 — [auto:milestone: 開始位置]

   milestone-4 / 進行中フェーズ: implement / 完了: design, test

   1. 進行中のimplementを続ける ← 推奨
   2. designからやり直す(/plan:design)

   どれにしますか?
   ```

3. 選択された開始位置から未完了フェーズを順に実行します(各コマンドの規約に従います)

   ```text
   design(/plan:design → design分commitの承認ゲート)
     → test(/build:test、commitしない)
     → implement(/build:implement、commitしない)
     → docs(/build:docs。残りの未commit差分をtest→feat→docsへ分割し、まとめて1回の
       承認ゲート。実装計画に次のsub-milestoneが残る場合はtest→implementを繰り返してから
       次のdocs実行で改めてまとめてcommitします。`build/docs.md`の次のステップの
       分岐に従います)
     → verify(/verify)
     → review(/review:code、上限3回)
     → ship(/ship:readiness → /ship:pr。fast-forward merge前に承認ゲート)
   ```

4. 承認ゲート(`/plan:design`のcommit直前、`/build:docs`の複数commit一括提示直前、
   `/ship:pr`のmerge直前)では意思決定レポートを送り、応答を待ちます
5. 各フェーズ完了時に`phase-state.json`を更新します(中断してもここから再開できます)
6. 完了時に、実行した検証・commit一覧・出荷結果・残存事項を報告します

## 停止条件

- 承認ゲートでの否認・方針変更の指示
- ループガードレールの定量上限
  ([`workflows.md 7.`](../../rules/workflows.md#7-ループガードレール))への到達
- 設計判断・依存追加が必要になった時点(PMへ委譲)
- 同じ失敗の繰り返しを検出した場合(ループを止めて原因を報告します)

---

次のステップ:

1. `/status` — 現在地の確認(中断からの再開もここから)
