---
name: handoff-check
description: 次フェーズを会話履歴なしで開始できるか検証する手順を定義する。/verify:handoffが参照する。
---

権限: `tmp-write`
副作用: `tmp/verify/YYYY-MM-DD-{phase}.md`の作成・上書き
承認: 不要です。

次フェーズを会話履歴なしで開始できるか検証する手順を定義します。

## フェーズ別確認表

| フェーズ | 読む文書 | 検証する能力 |
| --- | --- | --- |
| `requirements` | `docs/draft/project-direction.md`(Why/Who/What) | アーキテクチャ設計を始められるか |
| `architecture` | 上記 + `docs/draft/project-direction.md`(How) | マイルストーン分解または詳細設計を始められるか |
| `design` | 上記 + 対象`docs/milestones/m{N}-*.md` | テスト先行を始められるか |
| `implement` | 対象マイルストーン文書、対象ディレクトリのREADME.md | 実装を始められるか |
| `ship` | 差分、検証結果、レビュー結果 | 出荷フェーズへ進めるか |

## 会話履歴なし検証の実施手順

1. 対象フェーズに応じた文書セットのみを指定します
2. 会話履歴を参照せず、指定文書だけを読んで次フェーズが開始できるか判定します
3. 不足情報・暗黙知・補完が必要な箇所を具体的に列挙します
4. 文書を追加または更新し、再検証します

## レポート形式

`tmp/{work-dir}/handoff-check.md`または`tmp/verify/YYYY-MM-DD-{phase}.md`へ記録します。

```markdown
## Handoff検証: {phase}

### 判定: 開始できる / 開始できない / 人間判断が必要

### 不足している情報

- ...

### 暗黙知として残っている判断

- ...

### 補完が必要な箇所

- ...
```

## 注意事項

- [`agent-workflow/rules/workflows.md 5.`](../../rules/workflows.md#5-handoff契約)のHandoff契約の
  定義と整合させます
- 「開始できる」の判定は指定文書のみで完結することが条件です
