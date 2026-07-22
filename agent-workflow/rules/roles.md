# Roles / ロール定義

Roleは責務の単位であり、Agent(Claude / 他のAIツール / 人間)から独立して定義します。
どのAgentがどのRoleを担当するかは、コミットの`Role:`トレーラー([`naming-policy.md`](naming-policy.md))
またはIssue / PRへの記録を正本とします。

## 目次

- [1. Manager](#1-manager)
- [2. Architect](#2-architect)
- [3. Programmer](#3-programmer)
- [4. Reviewer](#4-reviewer)
- [5. Tester](#5-tester)
- [6. 割当の記録](#6-割当の記録)

## 1. Manager

- **責務:** 優先度決定、マイルストーン/フェーズ境界の承認、マージ順序の決定
- **範囲外:** 実装・レビューの実作業
- **実体(既定):** 人間(PM)+Manager補佐

## 2. Architect

- **責務:** 要件・設計・依存方向の決定、設計提案のStatus更新
- **範囲外:** 実装の作成、テストの実行
- **入力/出力:** マイルストーン・要件・アーキテクチャ文書 → 設計提案(`docs/draft/project-direction.md`、
  将来`docs/design/`)、Programmerへの委譲

## 3. Programmer

- **責務:** テスト先行の実施、実装、formatter・linter実行、commit(Prototype Modeは段階commit、
  Production ModeはPR作成)
- **範囲外:** 設計変更の承認、新しい依存の採用決定
- **入力/出力:** 承認済み設計提案 → 実装・テスト・commit/PR

## 4. Reviewer

- **責務:** レビューループプロトコル([`workflows.md 6.`](workflows.md#6-レビューループプロトコル))に従った品質確認
- **範囲外:** 設計変更の決定、実装の修正
- **実体(既定):** セッション内のsubagent

## 5. Tester

- **責務:** テスト計画、検証の実行、smoke確認、未解決事項の報告
- **範囲外:** 実装の修正、設計変更の承認
- **実体(既定):** セッション内のsubagentまたは`/verify`実行

## 6. 割当の記録

割当はcommitの`Role:`トレーラー、またはIssue / PRへ次の形式で記載します。チャット履歴を
割当の正本にしません。

```text
Role: Programmer
Agent: Claude
担当: @username または AI
```
