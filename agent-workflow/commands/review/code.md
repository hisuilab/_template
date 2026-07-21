管理責任: 差分のコードレビュー(Critical/High/Medium/Low分類)を行います。実装ファイルは
修正しません。
ワークフロー: review
状態確認先: `tmp/{work-dir}/code-review.md`

権限: `tmp-write`
副作用: `tmp/{work-dir}/code-review.md`の作成・上書き
承認: 不要です。

差分をレビューします。担当Role: Reviewer(subagentへ委譲)。

## 読み込む文書

1. 対象差分(`git diff`)を確認します
2. 変更されたディレクトリのREADME.md(概要/責任/責任外)を読み、責任範囲に沿った変更か
   確認します
3. 対象マイルストーン文書または設計提案のテスト方針を確認します

## 手順

1. 利用可能なsubagent機構でsubagent(権限: read-only / tmp-write)へ委譲し、
   レビューループプロトコル([`workflows.md 6.`](../../rules/workflows.md#6-レビューループプロトコル))
   で実行します。prefix: `code`
2. 評価軸: 責任分離、既存規約(design-maintainable-systemのDesign Rules)との整合、
   テストの妥当性、命名、重複
3. Critical/High/Medium/Lowに分類して指摘します
4. `tmp/{work-dir}/code-review.md`へ記録します

## 出力形式

```markdown
## レビュー: code — {work-dir}

### Critical

- ...

### High

- ...

### Medium

- ...

### Low

- ...

### 判定: 承認 / 要修正 / PM判断が必要
```

---

次のステップ:

1. 承認: `/ship:readiness`
2. 要修正: 指摘に対応後、再レビュー(上限3回)
