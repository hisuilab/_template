---
status: draft
created: 2026-07-11
updated: 2026-07-11
---

# Project Direction: _template

## 目次

- [1. 位置づけ](#1-位置づけ)
- [2. Why — 背景と動機](#2-why--背景と動機)
- [3. Who — 利用者](#3-who--利用者)
- [4. What — 提供する価値と機能](#4-what--提供する価値と機能)
- [5. Where — 適用範囲](#5-where--適用範囲)
- [6. When — フェーズと優先順位](#6-when--フェーズと優先順位)
- [9. 未解決の論点](#9-未解決の論点)

## 1. 位置づけ

`~/Projects/` 配下の新規プロジェクト立ち上げを効率化するための共通開発基盤テンプレートリポジトリです。
このリポジトリ自体がプロジェクト生成ツール（`tooling/`）と生成元となるProfile（`template/`）を提供します。

## 2. Why — 背景と動機

新規プロジェクトを起動するたびに、Nix flake・just・pre-commit・CI等の基盤を手動で構築していた。
`nix-station` にてこのテンプレートをベースとした開発を試み、基盤の有効性を確認済み。
nix-stationで蓄積された改善を取り込み、再利用可能な基盤として整備したい。

## 3. Who — 利用者

| 利用者 | 用途 |
| --- | --- |
| プロジェクト開始者（主にhisuilab） | 新規プロジェクトを生成コマンドで即座に立ち上げる |
| 既存プロジェクト管理者 | 基盤の更新を個別プロジェクトへ段階的に取り込む |

## 4. What — 提供する価値と機能

### 4.1. 共通開発基盤（実装済み）

| 機能 | 内容 |
| --- | --- |
| 再現可能な開発環境 | Nix flake によるdevShell |
| 統一フォーマット・lint | treefmt + rumdl |
| コミット品質ゲート | pre-commit（conventional-pre-commit, detect-secrets等） |
| タスクランナー | justfile |
| テスト | bats（シェルスクリプトユニットテスト） |
| CI | GitHub Actions（verify + check-readme） |
| 文書 status 検証 | `scripts/check-status`（docs/draft・milestones・decisions の frontmatter 妥当性） |

### 4.2. プロジェクト生成（今後実装）

- `tooling/` に生成ロジックを実装し、`template/` のProfileを読み込んで新規プロジェクト一式を出力します
- 生成されたプロジェクトは `just verify` で即座にグリーンになることを成功条件とします
- 呼び出し形式はアーキテクチャフェーズで確定します（既存README想定: `python3 -m tooling.generator generate --name ... --profile ... --output ...`）

### 4.3. Profileシステム（設計フェーズ）

スタイル × スケール × 用途の組み合わせでProfileを構成します。
各Profileはコンポーネントの組み合わせとして管理し、拡張性を確保します。

| 軸 | 候補値（暫定） |
| --- | --- |
| スタイル | prototype, layered, ddd |
| スケール | tiny, small, medium, large |
| 用途 | general, web, container, embedded |

## 5. Where — 適用範囲

| 対象 | 説明 |
| --- | --- |
| 生成先 | `~/Projects/<name>/` 配下の新規ディレクトリ |
| 生成元 | このリポジトリ（`_template`）の `template/` ディレクトリ |
| ターゲット環境 | macOS + Nix（nixpkgsベース） |

**対象外:**

- 既存プロジェクトへの自動マイグレーション
- Nix以外の環境向けパッケージング（将来検討）

## 6. When — フェーズと優先順位

| フェーズ | 内容 | 状態 |
| --- | --- | --- |
| フェーズ0 | 基盤共通部分の確立（flake/just/lint/CI/pre-commit） | 完了（nix-stationで検証済み） |
| フェーズ1 | nix-stationの改善バックポート + 要件・アーキテクチャ文書化 | 進行中 |
| フェーズ2 | `tooling/generator` の設計・実装（最小Profile: small） | 未着手 |
| フェーズ3 | Profileシステムの設計（スタイル×スケール×用途） | 未着手 |

## 9. 未解決の論点

| ID | 論点 | 影響範囲 | 優先度 |
| --- | --- | --- | --- |
| U-01 | `tooling/` の実装言語（Python想定だが未確定。Nix script / Rust等も候補） | tooling/ 設計 | 高 |
| U-02 | nix-stationの `config/`・`modules/` ディレクトリの位置づけ（共通化するか個別プロジェクト固有か） | template/ 設計 | 中 |
| U-03 | Profile（`template/`）の具体的なファイル構成（どのファイルを生成するか） | template/ 設計 | 中 |
| U-04 | スケール・スタイル・用途の具体的な候補値の確定 | Profileシステム設計 | 低（フェーズ3） |
| U-05 | 既存プロジェクト（nix-station等）への更新伝播方法 | 運用設計 | 低 |
