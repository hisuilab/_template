---
status: approved
proposed_at: 2026-07-13
approved_at: 2026-07-13
approved_by: PM
implemented_at: 2026-07-13
related: "#33"
---

# 意思決定の記録: workspace justfile の `nix run` 参照先をハードコードのまま維持する

## 目次

- [1. 背景と問題](#1-背景と問題)
- [2. 検討した選択肢](#2-検討した選択肢)
- [3. 採用案](#3-採用案)
- [4. 理由](#4-理由)
- [5. トレードオフと影響](#5-トレードオフと影響)

## 1. 背景と問題

`template/workspaces/default/justfile` の `new` レシピには `nix run github:hisuilab/_template -- create` がハードコードされています。`workspace.py` は `shutil.copy2` で直接コピーするため Renderer の変数置換が行われず、fork・リネーム・組織移管時に古いリポジトリ参照が配布されます。

## 2. 検討した選択肢

| # | 選択肢 |
| --- | --- |
| A | `workspace.py` にも Renderer の変数置換を通し、`{{template_repo}}` を `init-workspace` 呼び出し時に CLI 引数で注入する |
| B | このテンプレートは `hisuilab/_template` 専用であるという設計上の制約として Decision Record に記録し、justfile にコメントを追記する |

## 3. 採用案

選択肢 B — 設計上の制約として記録し、justfile にコメントを追記する

## 4. 理由

- このテンプレートは単一リポジトリ（`hisuilab/_template`）の配布物として設計されており、fork 対応は現時点のスコープ外です
- 変数置換の導入は `workspace.py` の責任拡大（Renderer 依存の追加）と CLI への新フラグ追加を伴い、実装・テスト・ドキュメントのコストが高い
- 生成された justfile は人間が直接編集するファイルであり、参照先の更新は fork 後のユーザーが1行変更するだけで完結します
- コメントで制約を明示することで、fork 時に何を変更すべきかが自明になります

## 5. トレードオフと影響

- fork したユーザーは `justfile` の `new` レシピを手動で更新する必要があります。コメントで案内します
- 将来 fork 対応が正式スコープになった場合は選択肢 A（変数置換）を再検討します。その際の実装起点は `workspace.py` の `shutil.copy2` をテンプレート展開に置き換えることです
