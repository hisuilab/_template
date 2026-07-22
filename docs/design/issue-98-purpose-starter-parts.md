---
status: proposed
proposed_at: 2026-07-22
approved_at: null
approved_by: null
implemented_at: null
related: "#98"
---

# 設計提案: 用途別starter複合Partとlang基盤依存の責任境界を定める

状態はfrontmatter(`status`・`proposed_at`・`approved_at`・`approved_by`・`implemented_at`・
`related`)が正本です。

## 目次

- [1. 問題](#1-問題)
- [2. 対象範囲](#2-対象範囲)
- [3. 選択肢](#3-選択肢)
- [4. 設計案](#4-設計案)
- [5. 失敗とロールバック](#5-失敗とロールバック)
- [6. 検証](#6-検証)
- [7. 未解決事項](#7-未解決事項)

## 1. 問題

`starter/<purpose>-<lang>`複合Partは#91で導入済みですが、当初はPythonコード混入の解消が
主目的でした。Web API、CLI、Database、foundationのような追加要求をどのPartレイヤーが
持つかは、Issue #98本文の時点では未整理です。

特に`lang/*`はdevShellツールの責務に閉じてきたため、生成プロジェクト自身が管理する
ランタイム依存(`pyproject.toml`、`package.json`、`Cargo.toml`、`go.mod`)をどこに置くかが
言語ごとに分散しています。RustとGoでは#100・#105で`lang/*`へ基盤依存を組み込む方針を
採用済みですが、PythonとTypeScriptには同等の判断がまだありません。

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| `starter/<purpose>-<lang>`を用途別実装の標準パターンとして確認 | 4言語×全starter用途の一括実装 |
| `lang/typescript`へ`package.json`を追加する前提整理 | `starter/*-typescript`の追加 |
| `starter/web-api-python`をFastAPI + httpxの最小Web APIへ拡張 | 本格的なルーティング、DB、認証、運用設定 |
| `features/foundation-python`の要否と初期スコープ判断 | Python全用途共通の設定・例外階層の作り込み |
| `features/database-<lang>`の扱いの判断 | database Partの実装、ORM/driver選定 |

## 3. 選択肢

| 案 | 内容 | 評価 |
| --- | --- | --- |
| A | `lang/*`は言語共通の最小プロジェクト基盤、`starter/<purpose>-<lang>`は用途別の即動く実装、`features/*`は後付けopt-in機能として分ける | ← 推奨。#91・#100・#105・#102・#107の既存判断と整合し、resolver/plannerの変更も不要です |
| B | `features/foundation-<lang>`を新設し、dotenvやエラー処理規約をすべてopt-inにする | 見送り。ほぼ全プロジェクトが必要とするマニフェストまでopt-inにすると、starter側で基盤依存を毎回合成する必要が出ます |
| C | 用途別starterだけで全ランタイム依存を管理する | 見送り。CLIやlibraryでも共通に必要なTypeScriptマニフェストなどが用途別Partへ重複します |

案Aを採用します。

## 4. 設計案

### 4.1. 責任境界

| 種別 | 責任 | 責任外 |
| --- | --- | --- |
| `lang/<lang>` | devShell、formatter/linter/test入口、言語共通マニフェスト、ほぼ全員が使う最小基盤依存 | Web API、CLI、library固有の依存やソース構成 |
| `starter/<purpose>` | lang非依存の用途別ディレクトリ骨格 | 言語固有のアプリケーション本体 |
| `starter/<purpose>-<lang>` | 選択した用途と言語の即動く最小実装、用途固有ランタイム依存 | database、認証、監視など横断的な後付け機能 |
| `features/<capability>-<lang>` | 既存生成物へ後から注入できるopt-in機能 | starterの初期構成を丸ごと置き換えること |

### 4.2. TypeScript共通前提

`lang/typescript`に`package.json`を追加します。TypeScriptの用途別Partが未実装でも、
`npx tsc`やnpm scriptsの置き場所を生成プロジェクトへ作るためです。

初期内容は次の最小構成にします。

```json
{
  "name": "{{project_name}}",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "type-check": "tsc --noEmit",
    "lint": "biome check .",
    "format": "biome check --write ."
  },
  "devDependencies": {
    "@biomejs/biome": "^2.0.0",
    "typescript": "^5.8.0"
  }
}
```

将来`starter/web-api-typescript`等が`package.json`を拡張する場合は、`strategy="replace"`で
累積的なスーパーセットを提供します。

### 4.3. Python Web API

`starter/web-api-python`は`pyproject.toml`と`src/app.py`を提供します。
`pyproject.toml`にはFastAPI、httpx、python-dotenv、uvicornを含めます。

```toml
[project]
name = "{{project_name}}"
version = "0.1.0"
description = "{{project_name}} web API service"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.116,<1",
  "httpx>=0.28,<1",
  "python-dotenv>=1,<2",
  "uvicorn[standard]>=0.35,<1",
]
```

`src/app.py`は`/health`のみを持つ最小ASGIアプリに留めます。ルーティング分割、設定クラス、
例外階層はプロジェクトごとの差が大きいため、今回のstarterには持ち込みません。

### 4.4. foundation Part判断

`features/foundation-python`は初期スコープでは作りません。Pythonの全用途共通マニフェストが
必要になった時点で`lang/python`へ`pyproject.toml`を追加し、用途別Partは必要に応じて
累積的な`pyproject.toml`で置き換えます。今回はWeb API用途だけが具体化しているため、
`pyproject.toml`は`starter/web-api-python`が持ちます。

dotenvはWeb APIのローカル設定読み込みでも使うため`starter/web-api-python`へ含めますが、
エラーハンドリング規約は具体化しません。規約だけを生成しても呼び出し元がなく、starterの
最小性を崩すためです。

### 4.5. database Part判断

DatabaseはWeb API、CLI、libraryのいずれにも後から併用しうる横断関心事です。そのため
`starter/database-*`や第4のstarter用途にはせず、将来必要になった時点で
`features/database-<lang>`として設計します。

## 5. 失敗とロールバック

- `lang/typescript`の`package.json`追加はファイル追加のみで、既存の生成パイプライン変更は不要です
- `starter/web-api-python`の`pyproject.toml`は同Partが選択された場合だけ生成されるため、
  CLIやlibraryのPython生成結果には影響しません
- `starter/web-api-python`を戻す場合は`pyproject.toml`追加と`src/app.py`更新をrevertします
- 後続の`starter/*-typescript`が`package.json`を置き換える場合は、`lang/typescript`側の
  devDependenciesとscriptsを落とさないスーパーセットにします

## 6. 検証

| テスト層 | 検証内容 |
| --- | --- |
| `tests/e2e/test_generate_profiles.py` | `--lang typescript`で`package.json`が生成されること |
| `tests/e2e/test_generate_profiles.py` | `--lang python`+`starter-web-api`でFastAPI/httpx等の依存と`/health`アプリが生成されること |
| `tests/unit/test_payload.py` | 追加payloadが空でなく、`{{project_name}}`が`part.toml`で宣言済みであること |
| `just verify` | formatter、文書検査、payload/schema/generatorテストをまとめて確認すること |

## 7. 未解決事項

- **TypeScript用途別Part**: `starter/web-api-typescript`や`starter/cli-typescript`は別Issueで実装します
- **Python共通pyproject**: CLI/libraryでも共通マニフェストが必要になった時点で`lang/python`へ移します
- **database Part**: `features/database-<lang>`は採用方針のみ確定し、具体的なORM/driver選定は
  database実装Issueで決定します
