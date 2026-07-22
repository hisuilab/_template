管理責任: テスト設計のレビュー(正常系・異常系・境界値の網羅性)を行います。
ワークフロー: review
状態確認先: `tmp/{work-dir}/test-review.md`

権限: `tmp-write`
副作用: `tmp/{work-dir}/test-review.md`の作成・上書き
承認: 不要です。

対象のテストをレビューします。担当Role: Reviewer(subagentへ委譲)。

## 読み込む文書

1. 対象テストファイルと対応する実装を確認します
2. 対象マイルストーン文書の完了条件を確認します

## 手順

1. 利用可能なsubagent機構でsubagent(権限: read-only / tmp-write)へ委譲します。prefix: `test`
2. 次を確認します: 正常系・異常系・境界値の網羅性、テストが対象を実際に検証しているか
   (弱いアサーション・過剰なモック化がないか)、対応するREADMEの「対応テスト」記載との一致
3. Critical/High/Medium/Lowに分類して`tmp/{work-dir}/test-review.md`へ記録します

---

次のステップ:

1. 承認: `/ship:readiness`
2. 要修正: `/build:test`でテストを追加・修正
