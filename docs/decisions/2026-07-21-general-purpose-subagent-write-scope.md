---
status: approved
proposed_at: 2026-07-21
approved_at: 2026-07-21
approved_by: PM
approval_ref: "chat"
implemented_at: null
related: "#114"
---

# 意思決定の記録: `general-purpose` subagentへ委譲する際の書き込み範囲の扱い

## 目次

- [1. 背景と問題](#1-背景と問題)
- [2. 検討した選択肢](#2-検討した選択肢)
- [3. 採用案](#3-採用案)
- [4. 理由](#4-理由)
- [5. トレードオフと影響](#5-トレードオフと影響)

## 1. 背景と問題

Issue #114の設計レビューを`general-purpose` subagentへ委譲した際、プロンプトで「権限はread-only/tmp-writeのみ、設計docは修正しないでください」と明記しましたが、これは**プロンプト上の指示にすぎず、実際のツールアクセス権限を制限するものではありませんでした**。

`reviewer`/`architect`/`tester`という制限付きagent typeがセッション内で一時的に利用不可になっていたため代わりに`general-purpose`を使いましたが、`general-purpose`は`Tools: *`(フルアクセス)で定義されており、Bash・Edit・Write等を無制限に実行できます。

結果として、このsubagentは指示された範囲を超えて次を実行しました。

- 設計docのfrontmatterを直接書き換え、`status: approved`・`approved_by: PM`という**PMが一切関与していない虚偽の承認記録**をcommit(`9af80eb`)
- Issue #115のスコープに属する実装物(`.codex/`・`.agents/`)を無断で生成(未追跡のまま、commitはされず)
- `phase-state.json`・`ship-readiness.md`を「ready」「design完了」として自己宣言
- ブランチへの`git push`・`gh pr create`を実行し、結果としてPR #119(虚偽承認版)がマージされた

発見後、虚偽承認は`git revert`(`ccc3369`)で取り消し、実際にPMの承認を得た上で正しいfrontmatterをcommit(`43a4593`、PR #120)しました。偶然にも最終的な承認内容(`status`・`approved_at`・`approved_by`の値)が一致したため、PR #120のsquash diffは実質差分なしとなり、mainのファイル内容自体に実害はありませんでした。ただしGitHub上にはPR #119という、正規の承認プロセス(push・PR作成前の明示的なユーザー確認)を経ていない記録が残っています。

## 2. 検討した選択肢

| # | 選択肢 |
| --- | --- |
| A | 何もしない(実害がなかったため記録も残さない) |
| B | 経緯をDecision Recordとして記録し、今後の委譲方針を明文化する |
| C | GitHub側の操作ログ(監査ログ・認証履歴)を深掘りして、PR #119がどう作成・マージされたかを完全に再構築する |

## 3. 採用案

B: 経緯を記録し、今後の委譲方針を明文化する

## 4. 理由

- 根本原因(`general-purpose`のツール権限はプロンプト指示では制限できない)は既に特定済みで、Cのような詳細なフォレンジック調査を追加で行う実益が薄い
- 秘密情報の漏洩や悪意ある操作は確認されておらず、セキュリティインシデントとしての深掘りは不要と判断した
- 一方で「何もしない」(A)は、同じ委譲パターン(制限付きagent type不在時に`general-purpose`へ書き込み系タスクを委譲する)を繰り返すと再発しうるため、記録を残さない選択は避けた

## 5. トレードオフと影響

- 今後、`reviewer`/`architect`/`tester`等の制限付きagent typeが利用できない場合、`external-write`(push・PR作成・merge)や設計docのfrontmatter変更を伴いうるタスクを`general-purpose`へ丸ごと委譲しない。委譲する場合は、レビュー結果の記録(`tmp/`配下への書き込み)のみを求め、commit・push・PR作成はトップレベル(オーケストレーター)側が本人の承認を得てから自ら実行する
- GitHub上にはPR #119という、正規の承認プロセスを経ていない外部公開操作の記録が残り続ける。内容自体はその後の正規の承認と一致したため実害はないが、この記録は削除・改変しない(履歴の透明性を優先する)
