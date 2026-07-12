---
status: in_progress
created: 2026-07-12
updated: 2026-07-12
---

# M4 エンドツーエンド統合と prototype → main PR

代表3プロファイル（small-cli / small-web-api / small-library）を生成し、生成プロジェクトの整合性を e2e テストで検証します。フェーズ2の完了マイルストーンとして `prototype → main` の PR を作成します。

## 目次

- [1. 概要](#1-概要)
- [2. 完了条件](#2-完了条件)
- [3. 設計](#3-設計)
- [4. 実装計画](#4-実装計画)
- [5. 前提とする未解決事項](#5-前提とする未解決事項)

## 1. 概要

状態はfrontmatter(`status`)が正本です（凡例: [`docs/milestones/README.md`](README.md)）。

| 項目 | 内容 |
| --- | --- |
| 依存 | M3（完了済み） |
| 目標 | 代表3プロファイルの生成が e2e テストで pass し、`prototype → main` PR が作成される |

e2e テストは check-readme / check-status / check-encoding（Nix 不要の bash スクリプト）で検証します。`nix develop --command just verify` による完全検証は手動確認手順として記録します。

## 2. 完了条件

- [x] `tests/e2e/test_generate_profiles.py` が追加され、3プロファイルの生成と check-readme / check-status / check-encoding の pass を pytest で確認する
- [x] `template/parts/base/payload/rumdl.toml` が追加されている（e2e テストで発覚した不足ファイル）
- [x] `pyproject.toml` の `testpaths` に `"tests/e2e"` が追加されている
- [x] e2e テストで発覚した問題がすべて修正されている
- [x] ルート `README.md` に生成コマンドの使用方法が追記されている
- [x] `just verify` pass（60件: bats 33 + unit 21 + e2e 13 - 先に 46 件だったが e2e 追加後 60 件）
- [ ] `nix develop --command just verify` が `~/Projects/foo`（small-cli 生成先）で pass する（手動確認）
- [ ] `prototype → main` PR が作成されている

## 3. 設計

### 3.1. e2e テスト方針

`tests/e2e/test_generate_profiles.py` に pytest テストを置きます。各テストは次の手順で実行します。

1. `tmp_path` に生成コマンドを実行してプロジェクトを出力する
2. 生成先で `git init && git add -A` を実行（check-readme は git で tracked files を発見する）
3. `bash scripts/check-readme`, `bash scripts/check-status`, `bash scripts/check-encoding` を subprocess で実行する
4. 期待するファイルの存在と内容を確認する

Nix が必要な `treefmt` や `rumdl check` は e2e テストの対象外とし、手動確認手順として記録します。

### 3.2. base payload の不足ファイル

M3 実装後の生成プロジェクト調査で、次の不足が判明しました。

| 不足ファイル | 影響 | 修正先 |
| --- | --- | --- |
| `rumdl.toml` | `just verify` の `check-docs` step が `rumdl.toml` を参照するが存在しない → エラー | `template/parts/base/payload/rumdl.toml` として追加 |

`rumdl.toml` の内容は `_template` リポジトリのものをベースに、`{{project_name}}` は不要（rumdl.toml はプロジェクト名に依存しない）。

### 3.3. ルート README.md の更新

「3. 構成」表の `tooling/` 行に説明を追記し、「2. クイックスタート」に生成コマンドを追加します。

```sh
# 新規プロジェクトを生成する（nix devShell 内で実行）
python3 -m tooling.generator generate \
  --name <project-name> \
  --profile small-cli \
  --output ~/Projects/<project-name>
```

### 3.4. prototype → main PR

M4 完了後、`prototype → main` PR を GitHub 上で作成します（Production Mode の `/ship:pr` に相当）。squash merge ではなく merge commit を使用します（`prototype` ブランチの commit 履歴を main へ取り込む）。

### 3.5. 手動確認手順

e2e テストで自動検証できない `nix develop --command just verify` の確認手順を記録します。

```sh
python3 -m tooling.generator generate \
  --name foo \
  --profile small-cli \
  --output ~/Projects/foo

cd ~/Projects/foo
nix develop --command just verify   # GREEN になることを確認
```

## 4. 実装計画

| # | 種別 | 内容 |
| --- | --- | --- |
| 1 | テスト | `tests/e2e/test_generate_profiles.py` 追加（RED 確認） |
| 2 | 修正 | `template/parts/base/payload/rumdl.toml` 追加 |
| 3 | 修正 | `pyproject.toml` の `testpaths` に `"tests/e2e"` 追加 |
| 4 | 確認 | e2e テスト GREEN 確認 |
| 5 | 文書 | ルート `README.md` 更新（生成コマンド追記） |
| 6 | 確認 | 手動: `~/Projects/foo` で `nix develop --command just verify` |
| 7 | 確認 | `just verify` pass |
| 8 | 出荷 | `/build:docs` + commit → `prototype` fast-forward merge → `prototype → main` PR |

## 5. 前提とする未解決事項

> [!NOTE]
> `docs/draft/project-direction.md` の「未解決の論点」のうち、本マイルストーンで扱わない範囲を示します。

- **U-04（スタイル・スケール候補値）**: M5+（フェーズ3）で扱います
- **U-05（既存プロジェクトへの更新伝播）**: 対象外
- **CI での e2e フル検証（nix develop + just verify）**: Nix ビルドに時間がかかるため M4 では CI に含めません。手動確認で代替します
