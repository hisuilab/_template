管理責任: なし(読み取り専用)。現在フェーズと次アクションの即答のみを行います。
ワークフロー: 横断(全フェーズから参照可能)
状態確認先: `tmp/{work-dir}/phase-state.json`、`docs/milestones/README.md`

権限: `read-only`
副作用: 画面出力のみ
承認: 不要です。

現在フェーズと次アクションを即答します。文書全体の読み込みは行いません。

## 読み込む文書

1. `tmp/{work-dir}/phase-state.json`(無い場合は空状態`{"completed": [], "skipped": [], "current": null}`)
2. `docs/milestones/README.md`(一覧・状態表)

## 手順

1. ブランチ名から作業の種別(milestone/issue)・IDとRigor Modeを検出します
   ([`workflows.md 1.`](../rules/workflows.md#1-作業単位とmode検出))。該当しない場合は
   プロジェクト全体の状態として扱います
2. `tmp/{work-dir}/phase-state.json`を読みます
3. `docs/milestones/README.md`の一覧表と照合し、現在地を導出します
4. 次の形式で表示します

   ```text
   📍 現在地

   Mode:   Prototype(branch: m1-validation-depth)
   単位:   milestone-1 「検証の深化」(なければ「未着手」)
   フェーズ: ✓ design → ✓ test → ▶ implement → □ docs → □ verify → □ review → □ ship
   ```

   記号: `✓`完了 / `▶`進行中 / `⊘`スキップ(理由付き) / `□`未着手

---

次のステップ:

1. 判定した現在フェーズのコマンド(例: `/build:implement`)
