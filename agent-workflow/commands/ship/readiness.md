管理責任: commit・push・PR作成の前に、出荷可能性を判定します。判定結果のみを記録し、
実際のcommit/push/PRは行いません。
ワークフロー: ship(判定)
状態確認先: `tmp/{work-dir}/ship-readiness.md`

権限: `tmp-write`
副作用: `tmp/{work-dir}/ship-readiness.md`の作成・上書き
承認: 不要です。

出荷可能性を判定します。担当Role: Reviewer。

## 読み込む文書

1. 対象マイルストーン文書(完了条件)またはIssue本文、`phase-state.json`、差分、
   レビュー結果、検証結果を確認します
2. [`workflows.md 1.`](../../rules/workflows.md#1-作業単位とmode検出)でRigor Modeを確認します

## 手順

1. 次のチェックを行います

   | 観点 | 完了条件 |
   | --- | --- |
   | スコープ | 差分が1論点に収まり、上限(8ファイル / 500行 / 新規5ファイル)を超えていない |
   | トレーサビリティ | マイルストーン/要件 → 設計 → テスト → 実装 → 文書の対応が追える |
   | テスト | `just verify`が成功し、未実行の検証が理由付きで説明できる |
   | レビュー | Critical / High指摘が0件。Medium / Lowはマイルストーン文書またはPR本文へ転記できる |
   | Audit Gate | マイルストーン完了前・リリース前(Production Mode)では`/review:audit`の未処理Critical / Highがない |
   | 承認 | 依存追加、外部公開、設計判断が必要ならPM判断済み |
   | 出荷文書 | 対象ディレクトリのREADME、必要なDecision Recordが同期している |
   | 文書同期 | `phase-state.json`の`docs`フェーズが`completed`または`skipped`(理由付き)である |

2. 判定を`ready` / `not_ready` / `needs_human`で出力します
3. `tmp/{work-dir}/ship-readiness.md`へ判定、根拠、残作業、未実行検証を記録します
4. `ready`の場合だけ`/ship:pr`を次ステップとして提示します

---

次のステップ:

1. ready: `/ship:pr`
2. not_ready: 指摘された修正コマンド
