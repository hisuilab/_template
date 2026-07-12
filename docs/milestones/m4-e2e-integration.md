---
status: not_started
created: 2026-07-12
---

# M4 エンドツーエンド統合と prototype → main PR

`tooling/generator` を使用して代表3プロファイルからプロジェクトを生成し、`just verify` グリーンを確認します。フェーズ2 の完了マイルストーンとして `prototype → main` の PR を作成します。

## 目次

- [1. 概要](#1-概要)
- [2. 完了条件](#2-完了条件)
- [3. 実装計画](#3-実装計画)
- [4. 前提とする未解決事項](#4-前提とする未解決事項)

## 1. 概要

状態はfrontmatter(`status`)が正本です（凡例: [`docs/milestones/README.md`](README.md)）。

| 項目 | 内容 |
| --- | --- |
| 依存 | M3（完了後） |
| 目標 | `python3 -m tooling.generator generate --name foo --profile small-cli --output ~/Projects/foo` の実行後、`cd ~/Projects/foo && just verify` がグリーンになる |

フェーズ2 の完了マイルストーンです。`prototype → main` の PR もここで作成します（Production Mode へ移行）。

## 2. 完了条件

- [ ] （M3 完了後に `/plan:design M4` で詳細化します）

## 3. 実装計画

| # | 種別 | 内容 |
| --- | --- | --- |
| 1 | テスト | e2e テスト（small-cli / small-web-api / small-library の各プロファイルで生成を実行し、生成先で `just verify` が pass することを確認） |
| 2 | 修正 | e2e テストで発覚した問題の修正 |
| 3 | 文書 | ルート `README.md` への生成コマンドの使用方法の記載 |
| 4 | 出荷 | `/ship:pr` で `prototype → main` PR 作成 |

## 4. 前提とする未解決事項

- **詳細設計**: M3 完了後に `/plan:design M4` で完了条件・設計を詳細化します
- **CI での e2e 検証**: GitHub Actions で生成コマンドを実行するかどうかは M4 設計時に決定します
