---
status: approved
proposed_at: 2026-07-13
approved_at: 2026-07-13
approved_by: PM
approval_ref: "prototype-mode-m10"
implemented_at: null
related: null
---

# 意思決定の記録: ワークスペース初期化を `init-workspace` サブコマンドとして提供する

## 目次

- [1. 背景と問題](#1-背景と問題)
- [2. 検討した選択肢](#2-検討した選択肢)
- [3. 採用案](#3-採用案)
- [4. 理由](#4-理由)
- [5. トレードオフと影響](#5-トレードオフと影響)

## 1. 背景と問題

`~/Projects` 配下でどこからでも `just`・`nix` を使えるように、親ディレクトリへの環境整備が必要になった。
提供方式として、ジェネレータへの統合か独立スクリプトかを選択する必要がある（U-09）。

## 2. 検討した選択肢

| # | 選択肢 |
| --- | --- |
| A | 既存ジェネレータ CLI に `init-workspace` サブコマンドを追加し、`template/workspaces/` の固定テンプレートを適用する |
| B | `scripts/` 配下に独立した Bash スクリプトとして実装する |
| C | 別バイナリ（別 `writeShellApplication`）として `flake.nix` に追加する |

## 3. 採用案

選択肢 A: `init-workspace` サブコマンド

## 4. 理由

- `nix run github:hisuilab/_template -- init-workspace --path ~/Projects` で `generate` と同じ呼び出し形式を維持できる
- applier などパイプラインの下流モジュールを再利用でき、保守コストが低い
- ユーザーが覚えるツールは1つで済む
- B 案（独立スクリプト）は `nix run` から呼べず、別途 `nix develop` が必要になる
- C 案（別バイナリ）はユーザーへの露出が増え、フレーク定義も複雑になる

## 5. トレードオフと影響

- `template/workspaces/` という新ディレクトリを追加する（`template/parts/` の Parts システムとは独立した固定テンプレート）
- `cli.py` に `init-workspace` サブコマンドを追加し、エントリポイントが薄くなるよう commands モジュールへ分離することを検討する
- Parts システム（resolver・planner）はワークスペース生成では使用しない（固定テンプレートのため）
