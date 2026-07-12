---
status: not_started
created: 2026-07-12
---

# M3 tooling/generator/ パイプライン実装

`template/parts/` の payload を読み込み、指定プロファイルからプロジェクトを生成する `tooling/generator/` パイプライン（loader / resolver / planner / renderer / applier）を実装します。

## 目次

- [1. 概要](#1-概要)
- [2. 完了条件](#2-完了条件)
- [3. 実装計画](#3-実装計画)
- [4. 前提とする未解決事項](#4-前提とする未解決事項)

## 1. 概要

状態はfrontmatter(`status`)が正本です（凡例: [`docs/milestones/README.md`](README.md)）。

| 項目 | 内容 |
| --- | --- |
| 依存 | M2（完了後） |
| 目標 | `python3 -m tooling.generator generate --name foo --profile small-cli --output /tmp/foo` が成功し、出力ディレクトリに期待するファイル一式が生成される |

対象は `tooling/generator/` のパイプライン実装とユニットテストです。CLI の完成と e2e テストは M4 で行います。

## 2. 完了条件

- [ ] （M2 完了後に `/plan:design M3` で詳細化します）

## 3. 実装計画

| # | 種別 | 内容 |
| --- | --- | --- |
| 1 | 新規 | `tooling/__init__.py` / `tooling/generator/__init__.py` |
| 2 | 新規 | `tooling/generator/models.py`（GenerateRequest / GenerationPlan / GenerationResult） |
| 3 | 新規 | `tooling/generator/errors.py`（LoadError / ResolveError / PlanError / RenderError / ApplyError） |
| 4 | 新規 | `tooling/generator/loader.py`（profile.toml / part.toml 読み込み） |
| 5 | 新規 | `tooling/generator/resolver.py`（Part 依存解決・順序決定） |
| 6 | 新規 | `tooling/generator/planner.py`（変数束縛・生成ファイル計画・競合検出） |
| 7 | 新規 | `tooling/generator/renderer.py`（`{{変数}}` 置換・ファイル名置換・staging 書き込み） |
| 8 | 新規 | `tooling/generator/applier.py`（staging → 出力先の原子的コピー） |
| 9 | 新規 | `tooling/generator/cli.py`（CLI エントリポイント） |
| 10 | 新規 | 各モジュールのユニットテスト |
| 11 | 確認 | `just verify` pass |

## 4. 前提とする未解決事項

- **詳細設計**: M2 完了後に `/plan:design M3` で完了条件・設計を詳細化します
- **flake.lock の扱い**: 生成後に `nix flake update` を実行するか、payload の flake.lock をそのままコピーするかは M3 設計時に決定します
