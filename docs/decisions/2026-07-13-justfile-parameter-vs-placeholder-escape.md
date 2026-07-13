---
status: implemented
proposed_at: 2026-07-13
approved_at: 2026-07-13
approved_by: PM
approval_ref: "https://github.com/hisuilab/_template/issues/40"
implemented_at: 2026-07-13
related: "#40"
---

# 意思決定の記録: just レシピパラメータと generator プレースホルダーの衝突回避

状態はfrontmatter(`status`・`proposed_at`・`approved_at`・`approved_by`・`implemented_at`・
`related`)が正本です。

## 目次

- [1. 背景と問題](#1-背景と問題)
- [2. 検討した選択肢](#2-検討した選択肢)
- [3. 採用案](#3-採用案)
- [4. 理由](#4-理由)
- [5. トレードオフと影響](#5-トレードオフと影響)

## 1. 背景と問題

`features/github-rulesets` Part の実装中に、just レシピのパラメータ構文 `{{param}}` が
generator(`src/generator.py`)のプレースホルダー正規表現 `r"\{\{(\w+)\}\}"` と衝突することが
判明しました。

`github-init visibility="private":` レシピ内で `gh repo create ... --"{{visibility}}"` と
記述すると、generator は `visibility` を未解決のプレースホルダーとして扱い
`RenderError: unresolved placeholder(s) ['visibility', 'preset'] in 'justfile'` を
発生させます。

## 2. 検討した選択肢

| # | 選択肢 |
| --- | --- |
| A | generator の正規表現を変更して just パラメータを除外する（例: `{{project_name}}` のみ許可するホワイトリスト） |
| B | 影響を受けるレシピを `#!/usr/bin/env bash` shebang 形式に変換し、`$param` 環境変数を使う |
| C | just パラメータを使わず、環境変数で代替する（shebang なしの通常レシピ） |

## 3. 採用案

**B: shebang 形式のレシピで `$param` 環境変数を使う**

just は shebang を持つレシピに対してパラメータを環境変数としてエクスポートします。
`{{param}}` の代わりに `$param` で参照できます。

## 4. 理由

- generator の正規表現を変更すると(A)、プレースホルダー検出の誤否定リスクが生じ、
  既存テンプレートの検証も困難になります
- shebang レシピ(B)は just の公式機能であり、bash の変数展開(`$param`)は generator の
  正規表現と無衝突です
- 通常レシピでの環境変数代替(C)は `export` 宣言が必要で、レシピのインターフェース(引数
  デフォルト値など)が失われます

## 5. トレードオフと影響

- 将来 just レシピに `{{param}}` を使う場合は、shebang 形式への変換が必要です
- generator のプレースホルダー構文と just のパラメータ構文の衝突は設計上の制約として
  `docs/decisions/` に残ります。将来 generator を拡張する際の既知制約です
- `lang/python` および `lang/typescript` の `strategy=replace` justfile にも同じ
  shebang 形式を適用しました（github-* レシピの完全複製が必要なため）
