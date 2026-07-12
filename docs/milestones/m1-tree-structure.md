---
status: done
---

# M1 template/ レイヤー設計とプロファイル骨格

拡張可能なコンポーネント構造（Parts/Profiles）の全体像を設計し、代表3プロファイルの宣言ファイルと生成ツリー仕様を確定する。

## 目次

- [1. 概要](#1-概要)
- [2. 完了条件](#2-完了条件)
- [3. レイヤー設計](#3-レイヤー設計)
- [4. template/ ツリー構造](#4-template-ツリー構造)
- [5. 代表プロファイルの生成ツリー](#5-代表プロファイルの生成ツリー)
- [6. 実装計画](#6-実装計画)
- [7. 前提とする未解決事項](#7-前提とする未解決事項)

## 1. 概要

状態はfrontmatter(`status`)が正本です（凡例: [`docs/milestones/README.md`](README.md)）。

| 項目 | 内容 |
| --- | --- |
| 依存 | なし（フェーズ1完了済み） |
| 目標 | `template/parts/` のレイヤー定義と代表3プロファイルの生成ツリーが確定し、profile.toml が作成されている |

対象は `template/` ディレクトリのレイヤー構造設計と宣言ファイル群です。Part の payload（実テンプレートファイル）の作成は M2 以降で行います。

## 2. 完了条件

- [ ] `template/parts/` のレイヤー一覧と各レイヤーの多重度制約が本文書に記載されている
- [ ] 代表プロファイル3種（`small-cli` / `small-web-api` / `small-library`）の `profile.toml` が作成されている
- [ ] 各プロファイルの生成後ディレクトリツリーが本文書 5節に記載されている
- [ ] `template/schema/` に ProfileSchema / PartSchema（dev-template からの移植）が配置されている
- [ ] `just verify` が pass する

## 3. レイヤー設計

Parts は以下のレイヤーで構成します。レイヤーは依存の浅い順に並べており、Resolver はこの順序で適用します。

| レイヤー | 多重度 | 責務 |
| --- | --- | --- |
| `base` | 必須 1 | 全 Profile 共通の開発基盤（Nix flake・just・pre-commit・CI・README 骨格） |
| `scale` | 必須 1 | スケール別の文書骨格（tiny / small / medium / large） |
| `purpose` | 必須 1 | 用途別の src/ 骨格とエントリポイント（cli / web-api / library） |
| `style` | 任意 0–1 | アーキテクチャパターン（prototype / layered / ddd）。省略時は purpose 提供のフラット構成を使用 |
| `languages` | 任意 0–n | 言語固有のツール設定（python / rust / …） |
| `features` | 任意 0–n | オプション機能（ai-agent / test-first-workflow / …） |

### 3.1. レイヤー間の依存ルール

```text
base → scale → purpose → style（任意）
                       → languages（任意）
                       → features（任意）
```

- `style/layered` と `style/ddd` は `scale/medium` 以上を推奨（`scale/small` でも利用可）
- `languages/*` は `purpose/*` と独立して組み合わせ可能
- 同一レイヤー内の Parts は互いに排他（例: `scale/small` と `scale/medium` は共存不可）

## 4. template/ ツリー構造

```text
template/
├── schema/                          # ProfileSchema / PartSchema（Python パッケージ）
│   ├── __init__.py
│   ├── _toml.py
│   ├── errors.py
│   ├── part_schema.py
│   └── profile_schema.py
├── profiles/                        # Profile 宣言（*.toml）
│   ├── small-cli.toml
│   ├── small-web-api.toml
│   └── small-library.toml
└── parts/                           # コンポーネント群（layer/name/）
    ├── base/
    │   ├── part.toml
    │   └── payload/                 # → M2 で実装
    ├── scale/
    │   ├── small/
    │   │   ├── part.toml
    │   │   └── payload/             # → M2 で実装
    │   └── …（tiny / medium / large は M3 以降）
    ├── purpose/
    │   ├── cli/
    │   │   ├── part.toml
    │   │   └── payload/             # → M2 で実装
    │   ├── web-api/
    │   │   ├── part.toml
    │   │   └── payload/             # → M2 で実装
    │   └── library/
    │       ├── part.toml
    │       └── payload/             # → M2 で実装
    ├── style/                       # → M3 以降
    ├── languages/                   # → M3 以降
    └── features/
        └── ai-agent/
            ├── part.toml
            └── payload/             # → M2 で実装
```

## 5. 代表プロファイルの生成ツリー

### 5.1. small-cli

```toml
[profile]
name = "small-cli"
summary = "小規模 CLI ツール向けプロファイル"
parts = ["base", "scale/small", "purpose/cli", "features/ai-agent"]

[variables]
```

**生成ツリー（目標設計）:**

```text
{{project_name}}/
├── .gitignore                   ← base
├── .pre-commit-config.yaml      ← base
├── AGENTS.md                    ← features/ai-agent
├── CLAUDE.md                    ← features/ai-agent
├── LICENSE                      ← base
├── README.md                    ← base
├── flake.nix                    ← base
├── flake.lock                   ← base
├── justfile                     ← base（purpose/cli がレシピ追加）
├── treefmt.nix                  ← base
├── docs/
│   └── draft/                   ← scale/small
├── scripts/
│   ├── check-readme             ← base
│   └── check-status             ← base
├── src/
│   └── main.py                  ← purpose/cli（エントリポイント骨格）
└── tests/
    └── unit/                    ← base
```

### 5.2. small-web-api

```toml
[profile]
name = "small-web-api"
summary = "小規模 Web API サービス向けプロファイル"
parts = ["base", "scale/small", "purpose/web-api", "features/ai-agent"]

[variables]
```

**生成ツリー（目標設計）:**

```text
{{project_name}}/
├── .gitignore                   ← base
├── .pre-commit-config.yaml      ← base
├── AGENTS.md                    ← features/ai-agent
├── CLAUDE.md                    ← features/ai-agent
├── LICENSE / README.md          ← base
├── flake.nix / flake.lock       ← base
├── justfile                     ← base（purpose/web-api がレシピ追加）
├── treefmt.nix                  ← base
├── docs/draft/                  ← scale/small
├── scripts/                     ← base
├── src/
│   ├── app.py                   ← purpose/web-api（アプリ起動骨格）
│   └── routes/                  ← purpose/web-api
└── tests/unit/                  ← base
```

### 5.3. small-library

```toml
[profile]
name = "small-library"
summary = "小規模ライブラリ・SDK 向けプロファイル（公開パッケージ想定）"
parts = ["base", "scale/small", "purpose/library", "features/ai-agent"]

[variables]
```

**生成ツリー（目標設計）:**

```text
{{project_name}}/
├── .gitignore                   ← base
├── .pre-commit-config.yaml      ← base
├── AGENTS.md                    ← features/ai-agent
├── CLAUDE.md                    ← features/ai-agent
├── CHANGELOG.md                 ← purpose/library（バージョン管理重視）
├── LICENSE / README.md          ← base
├── flake.nix / flake.lock       ← base
├── justfile                     ← base（purpose/library がレシピ追加）
├── treefmt.nix                  ← base
├── docs/draft/                  ← scale/small
├── scripts/                     ← base
├── src/
│   └── {{project_name}}/        ← purpose/library（パッケージ骨格）
│       └── __init__.py
└── tests/unit/                  ← base
```

## 6. 実装計画

| # | 種別 | 内容 |
| --- | --- | --- |
| 1 | 移植 | `template/schema/` を dev-template から移植（ProfileSchema / PartSchema） |
| 2 | 新規 | `template/parts/base/part.toml` 作成 |
| 3 | 新規 | `template/parts/scale/small/part.toml` 作成 |
| 4 | 新規 | `template/parts/purpose/cli\|web-api\|library/part.toml` 作成 |
| 5 | 新規 | `template/parts/features/ai-agent/part.toml` 作成 |
| 6 | 新規 | `template/profiles/small-cli\|small-web-api\|small-library.toml` 作成 |
| 7 | 確認 | schema で profile.toml を読み込み・バリデーション通過を確認 |
| 8 | 確認 | `just verify` pass |

## 7. 前提とする未解決事項

> [!NOTE]
> `docs/draft/project-direction.md` の「未解決の論点」のうち、本マイルストーンで扱わない範囲を示します。

- **U-02（src/ ディレクトリ）**: 本マイルストーンで廃止を決定。Part payload 内で必要な src/ は `purpose/*` の payload として提供するため、トップレベルの `src/` は M1 完了時に削除する
- **U-03（Profile の具体的なファイル構成）**: Part payload の中身（実ファイル）は M2 で確定する。本マイルストーンは宣言ファイル（part.toml / profile.toml）と設計ツリーの確定まで
- **U-04（候補値の確定）**: スタイル・スケール・用途の追加候補は M3 以降
- **U-05（既存プロジェクトへの更新伝播）**: 対象外
