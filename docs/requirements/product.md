# _template プロダクト要件

`~/Projects/` 配下の新規プロジェクト立ち上げを効率化する共通開発基盤テンプレートリポジトリの要件を定義します。

## 目次

- [1. 利用者と問題](#1-利用者と問題)
- [2. 提供価値](#2-提供価値)
- [3. 対象範囲](#3-対象範囲)
- [4. 対象外](#4-対象外)
- [5. 成功条件](#5-成功条件)
- [6. フェーズと優先順位](#6-フェーズと優先順位)

## 1. 利用者と問題

| 利用者 | 現状の問題 |
| --- | --- |
| プロジェクト開始者（主に hisuilab） | 新規プロジェクトを起動するたびに Nix flake・just・pre-commit・CI 等の基盤を手動で構築している |
| 既存プロジェクト管理者 | 基盤の改善を各プロジェクトへ個別に反映する手段がない |

## 2. 提供価値

- `just new myapp --profile <profile>` 1コマンドで再現可能な開発基盤付きプロジェクトを生成します
- プロジェクトの規模・アーキテクチャ・言語に応じたプロファイルを選択できます
- 生成直後から `nix develop` で言語ランタイムが使え、`just verify` がグリーンになります

## 3. 対象範囲

| 対象 | 説明 |
| --- | --- |
| 生成先 | `~/Projects/<name>/` 配下の新規ディレクトリ |
| 生成元 | このリポジトリ（`_template`）の `template/` ディレクトリ |
| ターゲット環境 | macOS + Nix（nixpkgs ベース） |
| プロファイル軸 | スケール（starter / small / medium / large）× アーキテクチャ（layered / ddd）× 言語（python / typescript） |

## 4. 対象外

- 既存プロジェクトへの自動マイグレーション（手動で Parts を注入する `inject` コマンドは別 Issue #59）
- Nix 以外の環境向けパッケージング
- Organization リポジトリ固有の設定

## 5. 成功条件

- [ ] 生成後に `nix develop --command just verify` がグリーンになる
- [ ] プロファイルごとの生成ファイル一覧が e2e テストで保証されている
- [ ] `just new` から非対話・対話の両方で生成できる

## 6. フェーズと優先順位

| フェーズ | 内容 | 状態 |
| --- | --- | --- |
| フェーズ0 | 基盤共通部分の確立（flake / just / lint / CI / pre-commit） | 完了 |
| フェーズ1 | nix-station 改善バックポート・Python/Ruff 環境整備 | 完了 |
| フェーズ2 | `tooling/generator` 実装・lang Part 追加（M1–M5） | 完了 |
| フェーズ3 | Biome・グローバル呼び出し・features Part 追加（M6–M10） | 完了 |
| フェーズ4 | `starter/*` 改名・`architecture/*` Part 追加・プロファイル再設計 | 進行中 |
| フェーズ5 | `inject` コマンド・複数 lang 対応・`scale/medium` 以上の docs | 未着手 |

詳細なマイルストーン一覧は [`docs/milestones/README.md`](../milestones/README.md) を参照してください。
