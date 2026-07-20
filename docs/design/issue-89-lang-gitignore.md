---
status: proposed
proposed_at: 2026-07-20
approved_at: null
approved_by: null
implemented_at: null
related: "#89"
---

# 設計提案: lang別.gitignoreの管理構造を整理する

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

`template/parts/base/payload/dot-gitignore`はlang非依存であるべき`base`層にもかかわらず、
Python専用の`__pycache__/`・`*.pyc`を無条件で含んでいます。一方`lang/typescript`の
`node_modules/`、`lang/rust`(#86)の`target/`はどのPartにも記述が無く、生成プロジェクトで
ビルド成果物がgit管理対象に混入するリスクがあります(#86のコードレビューでMedium指摘)。

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| `base`・`lang/python`・`lang/typescript`・`lang/rust`の`.gitignore`構成の是正 | ジェネレータへの新しい`file_rules`戦略(`"append"`)の追加(選択肢2として検討したが見送り) |
| 各langの生成プロジェクトに対するe2eテスト追加 | 将来の`lang/go`等の`.gitignore`対応（このIssueで確立したパターンに従うのみ） |

## 3. 選択肢

| 案 | 内容 | 評価 |
| --- | --- | --- |
| A | `base`の`.gitignore`からPython専用エントリを除去し、各`lang/*` Partが`flake.nix`と同じ`strategy="replace"`で自身の`dot-gitignore`（base共通内容+lang固有エントリ）を提供する | ← 推奨。既存のflake.nix/treefmt.nix/justfileの「lang毎に完全複製」パターンと完全に一貫し、ジェネレータへの機能追加が不要。既に3ファイルで実績のあるトレードオフ（base更新時は各lang Partへの反映が必要）をそのまま踏襲する |
| B | ジェネレータに真の内容追記マージ戦略（`"append"`）を新設し、base+lang各Partの`.gitignore`断片を結合する | 見送り。単一ユースケース（.gitignore）のために新しい抽象化を導入することになり、`policy.md`の「新しい抽象化にはcaller、contract、テストを要求します」に対して過剰投資。将来U-06（flake.nixの複数lang合成）で本格的な追記戦略が必要になった時点で、そちらの要件を含めて再設計する |

案Aを採用します。

## 4. 設計案

### 4.1. `base`の`dot-gitignore`（Python専用エントリを除去）

```text
# === 一時ファイル ===
.DS_Store
tmp/

# === Nix / direnv ===
.direnv/
result

# === AI エージェント設定 ===
.claude/

# === エディタ設定 ===
.vscode/
```

### 4.2. `lang/python`に`dot-gitignore`を追加（`strategy="replace"`）

base全文 + 以下を追加:

```text
# === Python ===
__pycache__/
*.pyc
```

### 4.3. `lang/typescript`に`dot-gitignore`を追加（`strategy="replace"`）

base全文 + 以下を追加:

```text
# === Node.js / TypeScript ===
node_modules/
```

### 4.4. `lang/rust`に`dot-gitignore`を追加（`strategy="replace"`）

base全文 + 以下を追加:

```text
# === Rust ===
target/
```

### 4.5. `part.toml`への`[[files]]`追加

3 Partすべてに以下を追加します（既存の`flake.nix`/`treefmt.nix`/`justfile`と同型）。

```toml
[[files]]
path = ".gitignore"
strategy = "replace"
```

`renderer.py`の`_strip_dot_prefix`により、payload上のファイル名`dot-gitignore`は生成先で
`.gitignore`に変換されます（`_transform_path`）。`[[files]].path`は変換後のdest_path空間
（`.gitignore`）で指定する必要があります（`_file_strategy`の照合ロジックに合わせる）。

## 5. 失敗とロールバック

- 既存の`lang/python`・`lang/typescript`利用者への影響は「無視されるファイルが増える」方向の
  みで、破壊的変更はありません
- `base`から`__pycache__/`・`*.pyc`を除去した直後に`lang`未指定でPythonプロジェクトを生成する
  ケースは現状存在しない（`--lang`は必須）ため後方互換の懸念はありません
- ロールバックは`git revert`で可能です

## 6. 検証

| テスト層 | 検証内容 |
| --- | --- |
| `tests/e2e/test_generate_profiles.py` | `--lang python`生成物の`.gitignore`に`__pycache__/`が含まれる／`--lang typescript`生成物に`node_modules/`が含まれる／`--lang rust`生成物に`target/`が含まれる |
| `tests/unit/test_schema.py` | 各`part.toml`の`[[files]]`追加がスキーマ検証を通ること（変更不要、既存の動的globで対象に入る） |
| `just verify`（このリポジトリ） | 全チェックpass |

## 7. 未解決事項

- **将来の`lang/go`対応**: 本Issueで確立したパターン（base全文+lang固有エントリを
  `strategy="replace"`で複製）にそのまま従う想定。設計判断は不要
- **U-06との関係**: 複数lang同時指定時の`.gitignore`合成は、flake.nixの`append`戦略と同じ
  タイミング（フェーズ5）でまとめて設計する
