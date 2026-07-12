---
status: done
created: 2026-07-12
updated: 2026-07-12
---

# M3 tooling/generator/ パイプライン実装

`template/parts/` の payload を読み込み、指定プロファイルからプロジェクトを生成する `tooling/generator/` パイプライン（loader / resolver / planner / renderer / applier）を実装します。

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
| 依存 | M2（完了済み） |
| 目標 | `python3 -m tooling.generator generate --name foo --profile small-cli --output /tmp/test-m3-foo` が成功し、出力ディレクトリに期待するファイル一式が生成される |

対象は `tooling/generator/` のパイプライン実装とユニットテストです。CLI の完成と e2e テスト（生成先での `just verify` 実行）は M4 で行います。

## 2. 完了条件

- [x] `tooling/__init__.py` / `tooling/generator/__init__.py` / `tooling/generator/__main__.py` が作成されている
- [x] `tooling/generator/models.py` に `GenerateRequest` / `PlannedFile` / `GenerationPlan` / `GenerationResult` が定義されている
- [x] `tooling/generator/errors.py` に `LoadError` / `ResolveError` / `PlanError` / `RenderError` / `ApplyError` が定義されている
- [x] `tooling/generator/loader.py` が `profile.toml` と `part.toml` を `ProfileSchema` / `PartSchema` として返す
- [x] `tooling/generator/resolver.py` が Part の `requires` 依存をトポロジカルソートし、循環依存を `ResolveError` で報告する
- [x] `tooling/generator/planner.py` が変数束縛・ファイル名プレースホルダー置換・`dot-` → `.` 変換後の `GenerationPlan` を返し、ファイル名衝突を `PlanError` で報告する
- [x] `tooling/generator/renderer.py` が `{{変数}}` を置換しながら staging ディレクトリへ書き込み、未置換変数を `RenderError` で報告する
- [x] `tooling/generator/applier.py` が staging → 出力先を原子的にコピーし、出力先既存を `ApplyError` で報告する
- [x] `tooling/generator/cli.py` に `generate` サブコマンドが実装されている
- [x] `tests/unit/test_generator.py` が各モジュールのユニットテストを含み、`pytest` で pass する
- [x] `python3 -m tooling.generator generate --name foo --profile small-cli --output /tmp/test-m3-foo` が成功し、出力に `.gitignore` / `flake.nix` / `justfile` / `src/main.py` が含まれている
- [x] `just verify` pass

## 3. 設計

### 3.1. パイプライン段階

各段階は純粋な変換として実装します（前段の出力が後段の入力になります）。

| 段階 | モジュール | 入力 | 出力 |
| --- | --- | --- | --- |
| LOAD | `loader.py` | profile_id, template_root | `ProfileSchema` + `list[PartSchema]` |
| RESOLVE | `resolver.py` | `list[PartSchema]` | トポロジカル順序の `list[PartSchema]` |
| PLAN | `planner.py` | `GenerateRequest` + `list[PartSchema]` | `GenerationPlan`（変数束縛 + `list[PlannedFile]`） |
| RENDER | `renderer.py` | `GenerationPlan` + staging_dir | staging ディレクトリへの書き込み |
| APPLY | `applier.py` | staging_dir + output_path | 出力先ファイルツリー |

### 3.2. データ型（models.py）

```python
@dataclass(frozen=True)
class GenerateRequest:
    name: str          # --name foo
    profile_id: str    # --profile small-cli
    output_path: Path  # --output ~/Projects/foo

@dataclass(frozen=True)
class PlannedFile:
    src_path: Path   # payload/ 内の絶対パス
    dest_path: str   # 出力先の相対パス（プレースホルダー・dot- 変換済み）
    strategy: str    # "error" | "replace"（M3スコープ）

@dataclass(frozen=True)
class GenerationPlan:
    request: GenerateRequest
    variables: dict[str, str]   # {"project_name": "foo", ...}
    files: tuple[PlannedFile, ...]  # Part 依存順に並んだ生成ファイル一覧

@dataclass(frozen=True)
class GenerationResult:
    output_path: Path
    files_written: tuple[str, ...]
```

### 3.3. ファイル名変換規則（PLAN 段階）

PLAN 段階でファイル名・ディレクトリ名を確定します。変換は次の順で適用します。

1. `{{変数}}` 置換（例: `src/{{project_name}}/` → `src/foo/`）
2. `dot-` プレフィックスの除去（例: `dot-gitignore` → `.gitignore`）

`dot-` 変換は M2 で payload dotfile を `dot-` 名で格納した際の規約（prek がライブ設定として誤認識するのを防ぐ）に対応するものです。

### 3.4. ファイル衝突と strategy（PLAN 段階）

同一 `dest_path` を複数の Part が提供した場合の動作です。

`part.toml` の `[[files]]` の `path` フィールドは、**変換後の dest_path 空間**（`dot-` 除去・プレースホルダー置換済み）で記述します。例: `dot-gitignore` の strategy を指定したい場合は `path = ".gitignore"` と書きます。

| strategy | 動作 |
| --- | --- |
| `error`（既定） | `PlanError` で停止し、競合ファイル名と関連 Part を報告 |
| `replace` | 後から処理する Part（トポロジカル順序で後位）のファイルで上書き |
| `append` | M5+ で実装（M3 スコープ外） |

### 3.5. staging による原子性（APPLY 段階）

- RENDER は `tempfile.mkdtemp()` の staging ディレクトリへ全ファイルを書き込みます
- APPLY は staging から出力先へコピーします。出力先ディレクトリが既存の場合は `ApplyError` で停止し、部分出力を残しません
- APPLY 中の I/O エラー時は部分出力をクリーンアップして `ApplyError` を送出します

### 3.6. flake.lock の扱い

`base/payload/flake.lock` を生成先へそのままコピーします。生成後に `nix flake update` を実行することでユーザーは最新の nixpkgs に追随できます。M3 の時点で `nix flake update` を自動実行する仕組みは持ちません（ネットワーク依存をテストに持ち込まないため）。

### 3.7. CLI エントリポイント

`python3 -m tooling.generator` で呼び出せるよう `tooling/generator/__main__.py` を作成します。

```text
python3 -m tooling.generator generate \
    --name <name> \
    --profile <profile_id> \
    --output <output_path>
```

`cli.py` は argparse によるサブコマンド分岐のみを持ち、ビジネスロジックは各パイプラインモジュールへ委譲します。

## 4. 実装計画

| # | 種別 | 内容 |
| --- | --- | --- |
| 1 | 新規 | `tooling/__init__.py` / `tooling/generator/__init__.py` / `tooling/generator/__main__.py` |
| 2 | 新規 | `tooling/generator/models.py`（GenerateRequest / PlannedFile / GenerationPlan / GenerationResult） |
| 3 | 新規 | `tooling/generator/errors.py`（LoadError / ResolveError / PlanError / RenderError / ApplyError） |
| 4 | 新規 | `tooling/generator/loader.py` + `tests/unit/test_generator.py::TestLoader`（RED→GREEN） |
| 5 | 新規 | `tooling/generator/resolver.py` + `TestResolver`（RED→GREEN） |
| 6 | 新規 | `tooling/generator/planner.py` + `TestPlanner`（RED→GREEN） |
| 7 | 新規 | `tooling/generator/renderer.py` + `TestRenderer`（RED→GREEN） |
| 8 | 新規 | `tooling/generator/applier.py` + `TestApplier`（RED→GREEN） |
| 9 | 新規 | `tooling/generator/cli.py` + 統合テスト `TestGeneratorIntegration`（small-cli 生成確認） |
| 10 | 更新 | `tooling/README.md`（実装内容を反映） |
| 11 | 確認 | `just verify` pass |

## 5. 前提とする未解決事項

> [!NOTE]
> `docs/draft/project-direction.md` の「未解決の論点」のうち、本マイルストーンで扱わない範囲を示します。

- **U-04（スタイル・スケール候補値）**: M5+（フェーズ3）で扱います
- **U-05（既存プロジェクトへの更新伝播）**: 対象外
- **`append` strategy**: 現在の代表3プロファイルでは使用しないため M5+ へ先送りします
- **flake.lock 自動更新**: M3 ではコピーのみ。自動 `nix flake update` は M5+ で検討します
