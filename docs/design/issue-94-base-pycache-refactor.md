---
status: implemented
proposed_at: 2026-07-20
approved_at: 2026-07-20
approved_by: PM
implemented_at: 2026-07-20
related: "#94"
---

# 設計提案: base の `__pycache__/` を lang/python 専有へ戻す（#91後の再評価）

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

`base`の`.gitignore`は`__pycache__/`・`*.pyc`を無条件で含んでいます。これは#89が
「`starter/*`がPython専用でlang非依存になっていない」ことを理由に採用した設計です。

しかし#91で`starter/cli`・`starter/web-api`・`starter/library`をlang非依存の骨格へ分割し、
`--lang`省略時・`--lang typescript`・`--lang rust`のいずれでもPythonソースが混入しなくなり
ました。#89が`base`に`__pycache__/`を残した前提は解消されています。

`.py`ファイルを生成しうる経路は、現在`lang/python`(`payload/tests/test_placeholder.py`)と
`starter/*-python`複合Part(`lang/python`と併用時のみ注入)に限られることを確認しました。
`features/ai-agent`・`features/github-rulesets`・`features/github-project`・
`features/logging-python`(いずれもデフォルトProfileには含まれないか、`.py`を含まない)にも
`.py`ファイルの無条件混入経路は無いことを確認済みです。

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| `base`・`lang/python`・`lang/typescript`・`lang/rust`の`.gitignore`構成の是正 | `lang/go`の追加(#87で別途対応。本Issue完了後に正しい前提で着手できる) |
| e2eテストの反転(`--lang`省略・typescript・rustで`__pycache__/`が含まれないことを検証) | ジェネレータへの新しい`file_rules`戦略の追加(不要) |

## 3. 選択肢

| 案 | 内容 | 評価 |
| --- | --- | --- |
| A | `base`から`__pycache__/`・`*.pyc`を除去し、`lang/python`が自身の`.gitignore`(base全文+`__pycache__/`・`*.pyc`)を`strategy="replace"`で提供する。`lang/typescript`・`lang/rust`からも`__pycache__/`行を削除する | ← 推奨。前回試みた設計と同じだが、#91により前提の安全性が確保されている |
| B | 現状維持(据え置き) | 見送り。不要なエントリが残り続け、Rust/TypeScript専用プロジェクトの`.gitignore`が不正確なまま |

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

base全文（4.1節の内容） + 以下を追加:

```text
# === Python ===
__pycache__/
*.pyc
```

`part.toml`に`[[files]] path = ".gitignore", strategy = "replace"`を追加します。

### 4.3. `lang/typescript`・`lang/rust`から`__pycache__/`・`*.pyc`を除去

両Partの`payload/dot-gitignore`から`__pycache__/`・`*.pyc`の2行を削除します(base全文の
コピー元が変わるため)。`node_modules/`・`target/`の固有エントリはそのまま維持します。

### 4.4. 前回の変更が失敗した理由と今回の違い

Issue番号#89の初版は「`--lang`省略時・`starter/*`経由でPythonソースが混入する既存の正規
パス」で`__pycache__/`が失われる回帰を起こしました。Issue番号#91はその混入経路自体を
塞いだため、今回は同じ変更が安全に行えます。この経緯は1節・関連Issueで明記し、同じ轍を
踏まないことをテスト(4.6節)で機械的に保証します。

### 4.5. `inject`経由の混入経路(レビューで発見)

`generate`コマンドの既定経路とは別に、`features/logging-python`(`src/logger.py`を同梱)は
`part.toml`の`requires = ["base"]`のみで`lang/python`を要求しないため、`--lang`未指定の
プロジェクトへ`just inject features/logging-python`で無条件に注入でき、`__pycache__/`が
無視されないまま`.py`ファイルが混入する経路が残っていました。`features/logging-python`・
`features/logging-typescript`の`requires`にそれぞれ`lang/python`・`lang/typescript`を
追加し、この経路を閉じます。`tests/e2e/test_inject.py`に
`test_inject_rejects_logging_python_without_lang_python`を追加し、回帰を機械的に検知します。

### 4.6. テストの反転

`tests/e2e/test_generate_profiles.py`の以下のテストを反転します。

| 既存テスト | 変更後 |
| --- | --- |
| `test_lang_omitted_gitignore_contains_pycache` | `test_lang_omitted_gitignore_does_not_contain_pycache`(`not in`へ反転) |
| `test_lang_typescript_gitignore_still_contains_pycache` | `test_lang_typescript_gitignore_does_not_contain_pycache`(`not in`へ反転) |
| `test_lang_rust_gitignore_still_contains_pycache` | `test_lang_rust_gitignore_does_not_contain_pycache`(`not in`へ反転) |

`test_lang_python_gitignore_contains_pycache`は変更しません(回帰確認として維持)。

## 5. 失敗とロールバック

- `--lang python`指定時の生成結果は`__pycache__/`を含む点で現状と同一(回帰なし)
- `--lang`省略・`--lang typescript`・`--lang rust`は「無視されるファイルが減る」方向の変更
  だが、対象言語のソースがそもそも生成されないため実害はない(4.1節で確認済み)
- `generate`経由だけでなく`inject`経由で`.py`/`.ts`を後から追加するPart
  (`features/logging-python`・`features/logging-typescript`)も、対応するlangの
  `requires`を持たない限り同種のリグレッションを再現しうる。4.5節の対応で
  `features/logging-*`は閉じたが、将来`.py`/`.ts`を同梱する新規Partを追加する際は
  対応するlangを`requires`へ含めることを設計時のチェック項目とする
- ロールバックは`git revert`で可能

## 6. 検証

| テスト層 | 検証内容 |
| --- | --- |
| `tests/e2e/test_generate_profiles.py` | 反転した3テスト+既存の`test_lang_python_gitignore_contains_pycache`(回帰確認) |
| `just verify`（このリポジトリ） | 全チェックpass |

## 7. 未解決事項

- **`lang/go`(#87)への適用**: 本Issue完了後、`lang/go`は最初から`__pycache__/`を含まない
  正しい前提(base全文+`.gitignore` go固有エントリ)で追加できます
- **U-06との関係**: 複数lang同時指定時の`.gitignore`合成は、flake.nixの`append`戦略と同じ
  タイミング（フェーズ5）でまとめて設計します
