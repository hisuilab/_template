# 文書の状態管理

## 目次

- [1. 対象と目的](#1-対象と目的)
- [2. 状態の一覧](#2-状態の一覧)
- [3. frontmatterの書式](#3-frontmatterの書式)
- [4. 状態遷移のタイミング](#4-状態遷移のタイミング)
- [5. 検証](#5-検証)

## 1. 対象と目的

ライフサイクルを持つ文書種別(draft・milestone・decision・design-proposal)は、ファイル
先頭のYAML frontmatterで状態を管理します。`grep "^status:"`だけで全種別を横断して
一撃検索できることを狙いとし、本文中に状態を重複して書きません。

## 2. 状態の一覧

| 種別 | 対象ディレクトリ | `status`の取りうる値 | 追加フィールド |
| --- | --- | --- | --- |
| draft | `docs/draft/` | `draft` → `migrated` | `migrated_at`・`migrated_to` |
| milestone | `docs/milestones/` | `not_started` → `in_progress` → `done` | (無し) |
| decision | `docs/decisions/` | `proposed` → `approved` → `implemented` | `proposed_at`・`approved_at`・`approved_by`・`implemented_at`・`related` |
| design-proposal | `docs/design/`(未実体化) | `proposed` → `approved` → `implemented` | 同上 |

`docs/milestones/README.md`の一覧表のような集約表は、frontmatterを手動転記した
スナップショットであり、実値はfrontmatter側が優先します。

## 3. frontmatterの書式

decision・design-proposalの例です(milestoneは`status`のみ、draftは`migrated_at`・
`migrated_to`のみを追加で持ちます)。

```yaml
---
status: proposed
proposed_at: 2026-07-10
approved_at: null
approved_by: null
implemented_at: null
related: null
---
```

## 4. 状態遷移のタイミング

| 種別 | 遷移 | 契機 |
| --- | --- | --- |
| draft | `draft` → `migrated` | 内容が正式文書(`docs/REQUIREMENTS.md`等)へ移行完了した時 |
| milestone | `not_started` → `in_progress` → `done` | 着手時、完了条件をすべて満たした時 |
| decision / design-proposal | `proposed` → `approved` → `implemented` | 提案時、PM承認時、実装完了時。承認時は`approved_by`も記録します |

移行済みのdraft・完了したmilestone・実装済みのdecisionも、ファイル自体は削除せず
判断の経緯として残します。

## 5. 検証

`scripts/check-status`が`just verify`の一部として、対象ディレクトリ配下の全ファイルに
frontmatterと有効な`status`値が存在するかを検証します。値が2節の一覧と一致しない場合は
`just verify`が失敗します。テンプレートの正本は`tmp/docs/_template/`(Git管理外の試験導入
ディレクトリ)です。
