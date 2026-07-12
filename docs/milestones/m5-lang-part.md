---
status: done
created: 2026-07-12
updated: 2026-07-12
---

# M5 lang/ Part 追加と --lang フラグ実装

`lang/python` および `lang/typescript` の言語環境 Part を追加し、生成コマンドに `--lang` フラグを導入します。生成プロジェクトで `nix develop` に入り言語ランタイムが即座に使える状態を保証し、フェーズ2の完了条件を満たして `prototype → main` PR を作成します。

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
| 依存 | M4（完了済み） |
| 目標 | `--lang python` で生成したプロジェクトで `nix develop` に入り `python3` が動き、`just verify` がグリーンになること |

M4 の手動確認で「生成プロジェクトに Python 環境が入っていない」問題が発覚。根本原因は base payload の `flake.nix` に言語ツールが含まれていないこと。本マイルストーンで `lang/` Part レイヤーを導入して解消します。

`--lang typescript` は devShell（Node.js + TypeScript）を提供しますが、TypeScript 用の purpose Part（`src/index.ts` 等）は M6+ です。`--lang typescript` で生成した場合、purpose Part は Python src/ を生成します（この組み合わせの実用性は M6+ の TypeScript 向け purpose Part 追加後に確保します）。

## 2. 完了条件

- [x] `models.py` に `LangSpec(lang: str, role: str | None)` データクラスが追加されている
- [x] `GenerateRequest` に `lang: tuple[LangSpec, ...]` フィールドが追加されている
- [x] `cli.py` が `--lang <value>` を必須引数として受け付ける
- [x] `--lang` 未指定時にエラー終了し、利用可能な lang 一覧を表示する
- [x] `--lang python,typescript` 等の複数指定（M5 時点）はエラー終了し、M6+ 対応予定の旨を表示する
- [x] `template/parts/lang/python/` が追加されている（part.toml + payload/）
- [x] `template/parts/lang/typescript/` が追加されている（part.toml + payload/）
- [x] `--lang python` で生成したプロジェクトで `nix develop --command python3 --version` が動く（手動確認）
- [x] `--lang python` で生成したプロジェクトで `nix develop --command just verify` がグリーンになる（手動確認）
- [x] `--lang typescript` で生成したプロジェクトで `nix develop --command node --version` が動く（手動確認）
- [x] e2e テストが `--lang python` を含むコマンドで全 pass する
- [x] `just verify`（このリポジトリ）が pass する
- [x] 生成 justfile に `just init`（git 初期化 + prek フックインストール）が追加されている
- [x] 生成 justfile に `just versions`（lang 別ツールバージョン一覧）が追加されている
- [x] 生成プロジェクトの README.md にセットアップ手順（`just init`）が記載されている
- [x] `prototype → main` PR が作成されている

## 3. 設計

### 3.1. LangSpec モデルと GenerateRequest 変更

```python
@dataclass(frozen=True)
class LangSpec:
    lang: str           # "python" | "typescript"
    role: str | None    # None = single/default, "backend" | "frontend" | "worker" = M6+

@dataclass(frozen=True)
class GenerateRequest:
    name: str
    profile_id: str
    output_path: Path
    lang: tuple[LangSpec, ...]  # 追加。M5 では要素数は常に 1
```

M5 では `lang` は必ず `(LangSpec(lang=<value>, role=None),)` の 1 要素タプルです。空タプルや複数要素は CLI でエラーとします。

### 3.2. CLI `--lang` パース仕様

| 入力 | 処理 | 結果 |
| --- | --- | --- |
| `--lang python` | `LangSpec(lang="python", role=None)` | OK |
| `--lang typescript` | `LangSpec(lang="typescript", role=None)` | OK |
| `--lang` 省略 | エラー終了 | "error: --lang is required. Available: python, typescript" |
| `--lang python,typescript` | エラー終了 | "error: multiple --lang values not supported in M5 (planned for M6+)" |
| `--lang backend=python` | エラー終了 | "error: role=lang syntax not supported in M5 (planned for M6+)" |
| `--lang go` | エラー終了 | "error: unknown lang 'go'. Available: python, typescript" |

利用可能な lang はジェネレータが `template/parts/lang/` を走査して動的に一覧化します。

### 3.3. lang Parts 注入フロー

CLI が `LangSpec` を生成した後、`profile.parts` リストへ `"lang/<lang>"` を末尾に追加してから Loader に渡します。Resolver 以降は変更なし。

```text
--lang python
  → profile.parts = ["base", "scale/small", "purpose/cli", "features/ai-agent"]
  → 注入後:   ["base", "scale/small", "purpose/cli", "features/ai-agent", "lang/python"]
  → Resolver がトポロジカルソート（lang/python が requires=["base"] を持つため base より後）
```

### 3.4. lang/python Part 構成

```text
template/parts/lang/python/
├── part.toml
└── payload/
    ├── flake.nix          ← base packages + python3, uv, ruff, pytest (strategy: replace)
    ├── treefmt.nix        ← base config + ruff (strategy: replace)
    ├── justfile           ← base recipes + test + verify に test を追加 (strategy: replace)
    └── tests/
        └── test_placeholder.py   ← pytest が exit 5 を返さないためのスタブ
```

**part.toml:**

```toml
[part]
id = "lang/python"
layer = "lang"
summary = "Python 言語環境（python3 / uv / ruff / pytest）"
requires = ["base"]
conflicts = ["lang/typescript"]

[[file_rules]]
path = "flake.nix"
strategy = "replace"

[[file_rules]]
path = "treefmt.nix"
strategy = "replace"

[[file_rules]]
path = "justfile"
strategy = "replace"
```

**justfile（lang/python 版）:**

```just
set shell := ["bash", "-euo", "pipefail", "-c"]

# requires: treefmt
format:
    treefmt

# requires: treefmt
lint:
    treefmt --fail-on-change

# requires: rumdl
check-docs:
    if [ -d docs ]; then rumdl check --config rumdl.toml docs/; fi

# requires: git
check-readme:
    ./scripts/check-readme

# requires: git
check-status:
    ./scripts/check-status

# requires: git
check-encoding:
    ./scripts/check-encoding

# requires: pytest
test:
    pytest

verify: lint check-docs check-readme check-status check-encoding test
```

**tests/test_placeholder.py:**

```python
# Generated placeholder — delete when you add real tests
def test_placeholder() -> None:
    pass
```

### 3.5. lang/typescript Part 構成

```text
template/parts/lang/typescript/
├── part.toml
└── payload/
    ├── flake.nix          ← base packages + nodejs, typescript (strategy: replace)
    ├── treefmt.nix        ← base config + prettier for .ts/.tsx (strategy: replace)
    └── justfile           ← base recipes + type-check (strategy: replace)
```

**part.toml:**

```toml
[part]
id = "lang/typescript"
layer = "lang"
summary = "TypeScript 言語環境（nodejs / typescript）"
requires = ["base"]
conflicts = ["lang/python"]

[[file_rules]]
path = "flake.nix"
strategy = "replace"

[[file_rules]]
path = "treefmt.nix"
strategy = "replace"

[[file_rules]]
path = "justfile"
strategy = "replace"
```

> [!NOTE]
> TypeScript 向け purpose Part（`src/index.ts` 等のスケルトン）は M6+ で追加します。M5 では `--lang typescript` と既存 purpose Part を組み合わせた場合、devShell は TypeScript 対応しますが `src/` は Python スケルトンのままです。

### 3.6. e2e テスト更新方針

既存 `tests/e2e/test_generate_profiles.py` の `_generate()` ヘルパーに `lang` 引数を追加します。

```python
def _generate(name: str, profile: str, output: Path, lang: str = "python") -> None:
    ...  # --lang <lang> を引数に追加
```

全既存テストはデフォルト `lang="python"` で動作継続します。新規テストとして以下を追加します。

| テスト | 検証内容 |
| --- | --- |
| `test_lang_required_error` | `--lang` 省略時に非ゼロ終了 |
| `test_lang_multiple_error` | `--lang python,typescript` でエラー終了 |
| `test_lang_python_flake_contains_python` | 生成 flake.nix に `python` パッケージ名が含まれる |
| `test_lang_typescript_flake_contains_nodejs` | 生成 flake.nix に `nodejs` が含まれる |

`nix develop` を使った runtime 確認はテスト対象外（手動確認）。

## 4. 実装計画

| # | 種別 | 内容 |
| --- | --- | --- |
| 1 | テスト | e2e テストに `lang` 引数を追加・新規テスト追加（RED 確認） |
| 2 | テスト | `test_generator.py` の `GenerateRequest` 生成箇所に `lang` 追加（RED 確認） |
| 3 | 実装 | `models.py` に `LangSpec` 追加・`GenerateRequest.lang` フィールド追加 |
| 4 | 実装 | `cli.py` に `--lang` 必須引数追加・パース・lang Parts 注入 |
| 5 | 実装 | `template/parts/lang/python/` 追加（part.toml + payload 4 ファイル） |
| 6 | 実装 | `template/parts/lang/typescript/` 追加（part.toml + payload 3 ファイル） |
| 7 | 確認 | e2e GREEN・`just verify` pass |
| 8 | 手動 | `~/Projects/foo`（small-cli + python）で `nix develop --command just verify` |
| 9 | 手動 | `~/Projects/bar`（small-cli + typescript）で `nix develop --command node --version` |
| 10 | 文書 | ルート README・tooling/generator/README 更新（--lang 追記） |
| 11 | 出荷 | commit → prototype fast-forward → `prototype → main` PR 作成 |

## 5. 前提とする未解決事項

> [!NOTE]
> `docs/draft/project-direction.md` の「未解決の論点」のうち、本マイルストーンで扱わない範囲を示します。

- **U-04（スタイル・スケール候補値）**: M6+（フェーズ3）で扱います
- **U-05（既存プロジェクトへの更新伝播）**: 対象外
- **U-06（append 戦略）**: M6+。複数 lang 指定・フルスタック構成はこの戦略が揃ってから実装します
- **U-07（役割名語彙）**: M6+
- **TypeScript 向け purpose Part**: M6+。`--lang typescript` と既存 purpose Part の組み合わせは devShell のみ対応（src/ は Python スケルトンのまま）
- **ランタイム検証の自動化**: e2e テストは `flake.nix` の文字列チェックのみで、`nix develop --command python3 --version` 等の実行確認はテスト対象外（手動確認）。Nix ビルドを CI に含める戦略（`@pytest.mark.slow` マークや専用ワークフロー）は M6+ で検討します
