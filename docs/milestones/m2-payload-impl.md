---
status: not_started
created: 2026-07-12
---

# M2 template/parts/ payload 実装

代表3プロファイル（small-cli / small-web-api / small-library）を生成するために必要なすべての Part payload を実装し、生成ツリーが検証テストで pass する状態にします。

## 目次

- [1. 概要](#1-概要)
- [2. 完了条件](#2-完了条件)
- [3. payload 設計](#3-payload-設計)
- [4. 実装計画](#4-実装計画)
- [5. 前提とする未解決事項](#5-前提とする未解決事項)

## 1. 概要

状態はfrontmatter(`status`)が正本です（凡例: [`docs/milestones/README.md`](README.md)）。

| 項目 | 内容 |
| --- | --- |
| 依存 | M1（完了済み） |
| 目標 | `template/parts/` の全 Part に payload ファイルを配置し、payload 整合テストが pass する |

M1 では `part.toml` / `profile.toml` の宣言ファイルと schema を実装しました。M2 では各 Part の `payload/` に実際のテンプレートファイルを配置し、生成ツールが読み込み可能な状態にします。

## 2. 完了条件

- [ ] `src/` ディレクトリが削除されている（U-02 解決）
- [ ] `base/payload/` に基盤ファイル一式が配置されている（`.gitignore` / `.pre-commit-config.yaml` / `LICENSE` / `README.md` / `flake.nix` / `flake.lock` / `justfile` / `treefmt.nix` / `scripts/check-readme` / `scripts/check-status` / `scripts/README.md` / `tests/unit/README.md`）
- [ ] `scale/small/payload/docs/draft/README.md` が配置されている
- [ ] `purpose/cli/payload/` に `src/main.py` / `src/README.md` が配置されている
- [ ] `purpose/web-api/payload/` に `src/app.py` / `src/routes/README.md` / `src/README.md` が配置されている
- [ ] `purpose/library/payload/` に `src/{{project_name}}/__init__.py` / `src/{{project_name}}/README.md` / `src/README.md` / `CHANGELOG.md` が配置されている
- [ ] `features/ai-agent/payload/` に `AGENTS.md` / `CLAUDE.md` が配置されている
- [ ] `tests/unit/test_payload.py` が追加され、payload 整合テストが pass する
- [ ] `just verify` が pass する

## 3. payload 設計

### 3.1. プレースホルダー方針

- `{{project_name}}` を唯一の変数とします（M2 スコープ内）
- プレースホルダーを含まないファイルはそのままコピーします
- ディレクトリ名にもプレースホルダーを使用できます（`src/{{project_name}}/` など）
- 各 payload サブディレクトリには `README.md` を置き、`_template` 自身の check-readme を満たしつつ、生成先プロジェクトの README としても機能させます

### 3.2. Part ごとの payload

| Part | 主な payload ファイル | `{{project_name}}` 使用箇所 |
| --- | --- | --- |
| `base` | `.gitignore` / `.pre-commit-config.yaml` / `LICENSE` / `README.md` / `flake.nix` / `flake.lock` / `justfile` / `treefmt.nix` / `scripts/check-readme` / `scripts/check-status` / `scripts/README.md` / `tests/unit/README.md` | `README.md` / `flake.nix` |
| `scale/small` | `docs/draft/README.md` | なし |
| `purpose/cli` | `src/main.py` / `src/README.md` | なし |
| `purpose/web-api` | `src/app.py` / `src/routes/README.md` / `src/README.md` | なし |
| `purpose/library` | `src/{{project_name}}/__init__.py` / `src/{{project_name}}/README.md` / `src/README.md` / `CHANGELOG.md` | `src/{{project_name}}/` ディレクトリ名 |
| `features/ai-agent` | `AGENTS.md` / `CLAUDE.md` | なし |

### 3.3. base payload の justfile

`base` の `justfile` は基盤レシピのみ（`verify` / `lint` / `check-docs` / `check-readme` / `check-status`）を含みます。`test-py` / `test-bats` は `languages/python` など言語 Part が追加する想定（M5+）のため、M2 では含めません。

### 3.4. payload 整合テスト（test_payload.py）

| テスト名 | 内容 |
| --- | --- |
| `test_payload_dir_exists_for_each_part` | `part.toml` が存在する各 Part に `payload/` ディレクトリがある |
| `test_placeholders_declared_in_part_toml` | payload ファイル内の `{{変数}}` がすべてその Part（または依存 Part）の `placeholders_required` に含まれる |
| `test_no_undeclared_placeholder_in_files` | `placeholders_required` を宣言していない Part の payload に `{{変数}}` が含まれない |

## 4. 実装計画

| # | 種別 | 内容 |
| --- | --- | --- |
| 1 | 削除 | `src/` ディレクトリを削除（U-02 解決） |
| 2 | 新規 | `tests/unit/test_payload.py` を追加（RED 確認） |
| 3 | 新規 | `base/payload/` にテンプレートファイル一式を配置 |
| 4 | 新規 | `scale/small/payload/docs/draft/README.md` を配置 |
| 5 | 新規 | `purpose/cli/payload/` ファイルを配置 |
| 6 | 新規 | `purpose/web-api/payload/` ファイルを配置 |
| 7 | 新規 | `purpose/library/payload/` ファイルを配置 |
| 8 | 新規 | `features/ai-agent/payload/` ファイルを配置 |
| 9 | 更新 | `template/README.md` をプロファイル名の実態に合わせて修正 |
| 10 | 確認 | `just verify` pass（payload 整合テスト GREEN） |

## 5. 前提とする未解決事項

> [!NOTE]
> `docs/draft/project-direction.md` の「未解決の論点」のうち、本マイルストーンで扱わない範囲を示します。

- **U-03（Profile の具体的なファイル構成）**: 本マイルストーンで確定します（3.2 節）
- **U-04（スタイル・スケール候補値の確定）**: M5+（フェーズ3）で扱います
- **U-05（既存プロジェクトへの更新伝播）**: 対象外
- **base justfile のレシピ範囲**: `test-py` 等は `languages/python` Part（M5+）が追加する想定。M2 では基盤レシピのみとします
