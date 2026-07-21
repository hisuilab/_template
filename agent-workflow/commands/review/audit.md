管理責任: リポジトリ全体をRed Team Auditとして横断監査します。マイルストーン完了宣言と
リリース前(Production Mode)に実行します。Prototype Modeでは必須にしません。
ワークフロー: review(Audit Gate)
状態確認先: `tmp/{work-dir}/audit-review.md`または`tmp/audit/YYYY-MM-DD-repository-audit.md`

権限: `tmp-write`
副作用: `tmp/{work-dir}/audit-review.md`または`tmp/audit/YYYY-MM-DD-repository-audit.md`の作成・上書き
承認: 不要です。

リポジトリ全体を横断監査します。担当Role: Reviewer(subagentへ委譲)。

## 読み込む文書

1. 対象マイルストーンが特定できる場合は対象文書、差分、`docs/decisions/`の関連判断を
   確認します。対象が無い場合はリポジトリ全体監査として、`AGENTS.md`、
   `docs/draft/project-direction.md`、`agent-workflow/rules/`、`docs/milestones/`、`tests/`、
   CI/pre-commit設定を確認します
2. 変更されたディレクトリのREADME.md一式を確認します

## 手順

1. 利用可能なsubagent機構でsubagent(権限: read-only / tmp-write)へ委譲し、
   レビューループプロトコル([`workflows.md 6.`](../../rules/workflows.md#6-レビューループプロトコル))
   で実行します。prefix: `audit`
2. 監査姿勢:
   - 大手テック企業の本番品質・設計レビュー・SREレビュー・セキュリティレビュー基準で
     厳しく評価します
   - 褒めることを目的にしません。構造的リスク、運用不能性、将来負債、AIエージェント
     運用リスクを優先して探します
   - 人格評価、努力への評価、悪口、抽象的な断定は禁止します
   - すべての指摘に優先度、対象、問題、影響、根拠、修正方針を必ず含めます
   - 根拠はファイル行、文書節、コマンド名、検証結果のいずれかへ紐づけます
3. 評価軸:
   - 要件定義、アーキテクチャ、責務分離、依存方向
   - 実装とドキュメントの整合性、正本の分離、更新運用
   - コード品質、テスト設計、CI / pre-commit、再現性
   - セキュリティ、権限、秘密情報、外部公開操作、サプライチェーン
   - 運用保守、障害時の回復、リリース、ロールバック
   - AIエージェント開発適性、コンテキスト分割、ガードレール、暴走防止
4. 出力形式:

   ```markdown
   # Audit Review

   ## 1. 総評

   ## 2. スコア

   | 項目 | スコア | 評価 |
   | --- | ---: | --- |
   | 要件定義 | 0-10 |  |
   | アーキテクチャ | 0-10 |  |
   | コード品質 | 0-10 |  |
   | テスト設計 | 0-10 |  |
   | ドキュメント整合性 | 0-10 |  |
   | 運用保守性 | 0-10 |  |
   | セキュリティ | 0-10 |  |
   | AIエージェント適性 | 0-10 |  |
   | 総合評価 | 0-10 |  |

   ## 3. Critical / High Findings

   | 優先度 | 対象 | 問題 | 影響 | 根拠 | 修正方針 |
   | --- | --- | --- | --- | --- | --- |

   ## 4. Medium / Low Findings

   | 優先度 | 対象 | 問題 | 影響 | 根拠 | 修正方針 |
   | --- | --- | --- | --- | --- | --- |

   ## 5. 次に直すべき順序
   ```

5. 対象が特定できる場合は`tmp/{work-dir}/audit-review.md`へ、特定できない場合は
   `tmp/audit/YYYY-MM-DD-repository-audit.md`へ記録します
6. Critical / High指摘は修正またはPM判断まで出荷を止めます。Medium / Lowはマイルストーン
   文書の「前提とする未解決事項」またはPR本文へ転記できます
7. 結果の要約とレポートパスを提示します

---

次のステップ:

1. Critical / Highあり: `/plan:design`または`/build:docs`
2. Critical / Highなし: `/ship:readiness`
