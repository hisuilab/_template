---
status: proposed
proposed_at: 2026-07-13
approved_at: null
approved_by: null
implemented_at: null
related: "#12"
---

# 設計提案: features/ai-agent Part 拡張（.claude/rules/dev-policy.md 追加）

## 目次

- [1. 問題](#1-問題)
- [2. 対象範囲](#2-対象範囲)
- [3. 選択肢](#3-選択肢)
- [4. 設計案](#4-設計案)
- [5. 失敗とロールバック](#5-失敗とロールバック)
- [6. 検証](#6-検証)
- [7. 未解決事項](#7-未解決事項)

## 1. 問題

`features/ai-agent` Part は `AGENTS.md`・`CLAUDE.md` のみを提供しており、生成プロジェクトで Claude が守るべき基本的な開発ポリシーが存在しない。[2026-07-13-ai-agent-claude-scope.md](../decisions/2026-07-13-ai-agent-claude-scope.md) で `.claude/rules/dev-policy.md` を最小構成として追加する方針が決定済み。

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| `features/ai-agent` payload への `dot-claude/rules/dev-policy.md` 追加 | `.claude/commands/`・`.claude/skills/` 等の _template 固有ファイル |
| Part README の更新 | 他の features Part |

## 3. 選択肢

アーキテクチャ設計済み（[Decision Record](../decisions/2026-07-13-ai-agent-claude-scope.md) 参照）。選択は確定。

## 4. 設計案

### ファイル構成

```text
template/parts/features/ai-agent/
├── part.toml          # 変更なし（requires = ["base"], conflicts = []）
├── README.md          # 更新：.claude/rules/dev-policy.md を責任に追記
└── payload/
    ├── AGENTS.md      # 変更なし
    ├── CLAUDE.md      # 変更なし
    └── dot-claude/
        └── rules/
            └── dev-policy.md  # 新規追加
```

`dot-` プレフィックスは planner.py が除去するため、生成先では `.claude/rules/dev-policy.md` として出力される。

### `dev-policy.md` の内容方針

- 「ファイルを読んでから変更する」
- 「変更は1つの目的に絞る」
- 「変更後は検証を実行して結果を報告する」
- 「明示的に依頼されるまでコミットしない」
- プロジェクト固有の規約は `AGENTS.md` に追記する運用をガイドする

プレースホルダー（`{{変数}}`）は使用しない。

## 5. 失敗とロールバック

| ケース | 影響 | 対応 |
| --- | --- | --- |
| `dot-claude/` が `.claude/` に変換されない | 生成先に `dot-claude/` ディレクトリが残る | planner.py の `dot-` 除去ロジックを確認 |
| `dev-policy.md` に `{{変数}}` が混入 | `test_no_undeclared_placeholders` が失敗 | プレースホルダーを使わない設計で回避 |

## 6. 検証

| 層 | 検証内容 |
| --- | --- |
| `tests/unit/test_payload.py` | `dot-claude/rules/dev-policy.md` が payload に存在する |
| `tests/e2e/test_generate_profiles.py` | `features/ai-agent` を含む Profile を生成すると `.claude/rules/dev-policy.md` が出力される |

## 7. 未解決事項

なし（アーキテクチャ設計で解消済み）。
