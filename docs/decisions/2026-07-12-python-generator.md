---
status: approved
proposed_at: 2026-07-12
approved_at: 2026-07-12
approved_by: PM
implemented_at: null
related: null
---

# 意思決定の記録: ジェネレータ実装言語として Python 3.11+ を採用

## 目次

- [1. 背景と問題](#1-背景と問題)
- [2. 検討した選択肢](#2-検討した選択肢)
- [3. 採用案](#3-採用案)
- [4. 理由](#4-理由)
- [5. トレードオフと影響](#5-トレードオフと影響)

## 1. 背景と問題

`tooling/generator` の実装言語を確定する必要があった。
先行リポジトリ `dev-template` が Python で完全実装されており、流用可否を確認した。

## 2. 検討した選択肢

| # | 選択肢 |
| --- | --- |
| A | Python 3.11+（標準ライブラリのみ） |
| B | Bash スクリプト（devShell 追加なし） |
| C | Nix スクリプト（Nix ネイティブ） |

## 3. 採用案

選択肢 A: Python 3.11+

## 4. 理由

- `dev-template` に動作実績のある実装（loader / resolver / planner / renderer / applier）が存在し、そのまま流用できる
- 標準ライブラリのみ使用のためサードパーティ依存なし（pytest は devShell のテスト用途のみ）
- Nix devShell への追加コストが小さい（`pkgs.python3` + `pkgs.python3Packages.pytest` の 2 行）
- ファイル生成・テキスト置換・TOML 読み込みが標準ライブラリで完結する

## 5. トレードオフと影響

- Bash 案と比べて devShell に Python ランタイムが加わるが、nixpkgs 標準パッケージであり保守コストは低い
- Nix 案と比べて Nix 固有の評価モデルを回避でき、可読性・テスタビリティが高い
- Python バージョンアップ時は `pyproject.toml` の `requires-python` と `flake.nix` の `pkgs.python3` を合わせて更新する
