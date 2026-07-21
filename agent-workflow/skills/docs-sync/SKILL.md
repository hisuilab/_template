---
name: docs-sync
description: 実装・設計・運用方針と文書を同期する手順と観点を定義する。/build:docsが参照する。
---

権限: `source-write`
副作用: README.md・`docs/`配下の更新
承認: 新規文書の追加・大規模再編はPM確認が必要です。

実装・設計・運用方針と文書を同期する手順と観点を定義します。

## 同期対象文書リスト

| 文書 | 確認観点 |
| --- | --- |
| 変更ディレクトリのREADME.md | 概要・責任・責任外が実装と一致しているか |
| `docs/draft/project-direction.md` | 仕様変更がある場合、Why/Who/What/Howが更新されているか。frontmatterの`status`が実態と一致しているか |
| `docs/milestones/README.md` / `docs/milestones/m{N}-*.md` | 状態・完了条件・実装計画が現状を反映しているか |
| `docs/decisions/` | 大きな判断があった場合、新規Decision Recordが作成されているか |
| `agent-workflow/rules/` | AI協働規約・権限・命名・ワークフローが実運用と一致しているか |

## 文書間リンク・目次・文体の確認手順

1. 見出し変更がある場合、文書内・文書間のアンカーリンクを更新します
2. 複数の主要節を持つ文書には番号付き・リンク付き目次があるか確認します
3. 日本語の説明文は「です・ます調」に統一されているか確認します(`AGENTS.md`)
4. 表・Mermaid・NOTE/TIP/IMPORTANT/WARNINGの使用が適切か確認します

## 文書frontmatterの確認手順

[`docs/development/document-status.md`](../../../docs/development/document-status.md)に
従い、draft・milestone・decision・design-proposalの各frontmatter(`status`等)を実態に
合わせて更新します。値の妥当性は`scripts/check-status`が`just verify`で検証します。

## `just verify`の実行手順

1. `just verify`を実行して全チェックが通過することを確認します
2. 失敗した場合は原因を特定して修正します
3. 修正後に再度`just verify`を実行して通過を確認します

## 注意事項

- commitは行いません(呼び出し元コマンドが管理します)
- 同期が不要な文書は「変更なし」と明示します
