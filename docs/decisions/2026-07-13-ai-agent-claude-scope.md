---
status: approved
proposed_at: 2026-07-13
approved_at: 2026-07-13
approved_by: PM
approval_ref: "prototype-mode-m9"
implemented_at: null
related: null
---

# 意思決定の記録: `features/ai-agent` Part の汎用化スコープ

## 目次

- [1. 背景と問題](#1-背景と問題)
- [2. 検討した選択肢](#2-検討した選択肢)
- [3. 採用案](#3-採用案)
- [4. 理由](#4-理由)
- [5. トレードオフと影響](#5-トレードオフと影響)

## 1. 背景と問題

生成されたプロジェクトに AI 開発ガイドラインを提供したい。現行の `features/ai-agent` Part は `AGENTS.md`・`CLAUDE.md` のみを提供しているが、`.claude/commands/`・`.claude/rules/` 等の AI ワークフロー設定ファイル群をどこまで生成対象に含めるかが未確定だった（U-08）。

`_template` 自身の `.claude/` 配下は実験的な試験運用中であり、全ファイルをそのまま生成対象にするのはリスクが高い。

## 2. 検討した選択肢

| # | 選択肢 |
| --- | --- |
| A | `AGENTS.md`・`CLAUDE.md` のみ（現行維持）に加え、`.claude/rules/dev-policy.md` だけを追加する |
| B | `_template` の `.claude/commands/`・`.claude/rules/` 全体を汎用テンプレートとして整備し、生成対象に含める |
| C | `.claude/` は一切生成せず、`AGENTS.md`・`CLAUDE.md` に留める |

## 3. 採用案

選択肢 A: 最小限の `.claude/` scaffold を追加する

## 4. 理由

- `_template` の `.claude/rules/` は Prototype/Production モード・マイルストーン番号・Issue 番号など `_template` 固有の概念を含み、汎用プロジェクトへそのまま適用できない
- `AGENTS.md`（コミット規約）と軽量な AI 開発ポリシー（`.claude/rules/dev-policy.md`）は言語・規模に依存しないため汎用化できる
- `.claude/` が安定したら段階的に拡張できる。初回から全ファイルを含めると、後から削除するのが難しい
- B 案は `.claude/` の内容が確定していない現段階では保守負荷が高い

## 5. トレードオフと影響

- 生成プロジェクトでは `AGENTS.md`・`CLAUDE.md`・`.claude/rules/dev-policy.md` の3ファイルが提供される
- `.claude/rules/dev-policy.md` は「ファイルを読んでから変更する」「検証結果を報告する」程度の最小ポリシーとし、プロジェクト固有の規約は生成後に手動で追加する運用とする
- 将来的に commands/skills を標準化できた段階で M9 の発展版として再設計する余地を残す
