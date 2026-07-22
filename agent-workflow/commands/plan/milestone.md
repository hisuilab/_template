管理責任: マイルストーンの作業ブランチを確定し、実装フェーズへ引き渡せる状態を作ります。
ワークフロー: plan(マイルストーン開始)
状態確認先: `tmp/milestone-{N}/phase-state.json`

権限: `git-commit`
副作用: `m{N}-slug` ブランチの作成、`tmp/milestone-{N}/phase-state.json` の初期化
承認: ブランチ名を提示し、承認後に作成します

マイルストーンの作業ブランチを確定します(Prototype / Production 両対応)。担当Role: Programmer。

## 前提条件

- `docs/milestones/m{N}-*.md` が存在すること(マイルストーン設計が完了していること)
- `prototype` ブランチまたは既存の `m{N}-slug` ブランチ上で実行すること

## 読み込む文書

1. `docs/milestones/README.md` で対象マイルストーンの状態を確認します
2. 対象 `docs/milestones/m{N}-*.md` で slug とステータスを確認します

## 手順

1. 引数からマイルストーン番号 N を取得します(例: `/plan:milestone 4` → N=4)
   引数がない場合は `docs/milestones/README.md` を参照し、最初の未着手マイルストーンを提案します
2. `docs/milestones/m{N}-*.md` を読み、slug を取得します
3. 作成するブランチ名 `m{N}-{slug}` を意思決定レポートで提示し、承認を得ます

   ```text
   📋 意思決定 — [plan:milestone: ブランチ作成]

   m4-stack-simplification ブランチを prototype から作成します

   1. 作成する ← 推奨
   2. slug を変更する

   どれにしますか?
   ```

4. `git checkout -b m{N}-{slug}` を実行します
5. `tmp/milestone-{N}/` を作成し、`phase-state.json` を初期化します

   ```json
   {
     "completed": [],
     "skipped": [],
     "skip_reasons": {},
     "current": null
   }
   ```

6. 次のステップを案内します

---

次のステップ:

1. `/auto:milestone` — 全フェーズを自動実行
2. `/plan:design` — 実装設計から始める
