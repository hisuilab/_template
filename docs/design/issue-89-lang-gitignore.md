---
status: implemented
proposed_at: 2026-07-20
approved_at: 2026-07-20
approved_by: PM
implemented_at: 2026-07-20
related: "#89"
---

# 設計提案: lang別.gitignoreの管理構造を整理する

状態はfrontmatter(`status`・`proposed_at`・`approved_at`・`approved_by`・`implemented_at`・
`related`)が正本です。

> [!NOTE]
> `/review:code`で「`base`をlang非依存に純化する」という初版の前提がCriticalとして指摘されました
> (`--lang`は必須ではなく、`starter/*`はlang非依存になっていないためPythonソースが無条件で
> 混入する)。本版はその指摘を反映した修正版です。初版との差分は`git log -p`で追えます。

## 目次

- [1. 問題](#1-問題)
- [2. 対象範囲](#2-対象範囲)
- [3. 選択肢](#3-選択肢)
- [4. 設計案](#4-設計案)
- [5. 失敗とロールバック](#5-失敗とロールバック)
- [6. 検証](#6-検証)
- [7. 未解決事項](#7-未解決事項)

## 1. 問題

`lang/typescript`には`node_modules/`を、`lang/rust`(#86)には`target/`を無視する`.gitignore`
設定が無く、生成プロジェクトでビルド成果物がgit管理対象に混入するリスクがあります(#86の
コードレビューでMedium指摘)。

初版は「`base`の`.gitignore`はlang非依存であるべき」という前提で`__pycache__/`・`*.pyc`を
`base`から除去する設計でしたが、レビューでCriticalとして指摘された通りこの前提は誤りでした。
`--lang`は`tooling/generator/cli.py`上必須ではなく(`default=None`)、`starter/cli`等の
Profileは`lang/*`へ依存せずに`src/main.py`(Python)を無条件で同梱します(TypeScript向け
purpose Partが無いM5以来の既知のギャップ)。つまり`--lang`を省略しても、あるいは
`--lang typescript`/`--lang rust`を指定してもPythonソースが生成されるため、`__pycache__/`は
現時点では実質的に全プロファイル共通で必要です。`starter/*`がlang非依存になるまでは、
`base`から除去できません。

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| `lang/typescript`への`node_modules/`追加、`lang/rust`(#86マージ後の別コミット)への`target/`追加 | `base`の`__pycache__/`・`*.pyc`の除去(`starter/*`がPython非依存になるまで対象外) |
| 各langの生成プロジェクトに対するe2eテスト追加(`--lang`省略パスを含む) | ジェネレータへの新しい`file_rules`戦略(`"append"`)の追加(選択肢2として検討したが見送り) |

## 3. 選択肢

| 案 | 内容 | 評価 |
| --- | --- | --- |
| A | `base`の内容はそのまま(`__pycache__/`維持)にし、`lang/typescript`(・将来`lang/rust`)が`flake.nix`と同じ`strategy="replace"`で「base全文+lang固有エントリ」の`dot-gitignore`を提供する | ← 推奨。既存のflake.nix/treefmt.nix/justfileの「lang毎に完全複製」パターンと一貫し、ジェネレータへの機能追加が不要。`base`の不変条件(全プロファイルに影響)を壊さない |
| B | ジェネレータに真の内容追記マージ戦略（`"append"`）を新設し、base+lang各Partの`.gitignore`断片を結合する | 見送り。単一ユースケース（.gitignore）のために新しい抽象化を導入することになり、`policy.md`の「新しい抽象化にはcaller、contract、テストを要求します」に対して過剰投資。将来U-06（flake.nixの複数lang合成）で本格的な追記戦略が必要になった時点で、そちらの要件を含めて再設計する |
| C(初版・撤回) | `base`からPython専用エントリを除去し、`lang/python`にも専用`dot-gitignore`を持たせる | 撤回。`--lang`省略時・`starter/*`経由でPythonソースが混入する既存の正規パスに対し`__pycache__/`の無視設定が失われる回帰を生む(レビューCritical指摘) |

案Aを採用します。

## 4. 設計案

### 4.1. `base`の`dot-gitignore`（変更なし。`__pycache__/`・`*.pyc`を維持）

```text
# === 一時ファイル ===
.DS_Store
tmp/
__pycache__/
*.pyc

# === Nix / direnv ===
.direnv/
result

# === AI エージェント設定 ===
.claude/

# === エディタ設定 ===
.vscode/
```

`starter/*`がlang非依存になっていない現状では、`__pycache__/`は`--lang`の値によらず全生成
プロジェクトに必要です。`lang/python`は独自の`dot-gitignore`を持たず、`base`のものをそのまま
使います(差分がないため)。

### 4.2. `lang/typescript`に`dot-gitignore`を追加（`strategy="replace"`）

base全文（`__pycache__/`含む）+ 以下を追加:

```text
# === Node.js / TypeScript ===
node_modules/
```

### 4.3. （#86マージ後・別コミット）`lang/rust`に`dot-gitignore`を追加

base全文（`__pycache__/`含む）+ 以下を追加:

```text
# === Rust ===
target/
```

`lang/rust`(#86)は本Issueの時点で`main`未マージのため、本Issueでは適用できません。#86の
ブランチを本Issueマージ後の`main`へrebaseする際に、このパターンに従う追加コミットとして
適用します。

### 4.4. `part.toml`への`[[files]]`追加

`lang/typescript`（・将来`lang/rust`）に以下を追加します（既存の`flake.nix`/`treefmt.nix`/
`justfile`と同型）。

```toml
[[files]]
path = ".gitignore"
strategy = "replace"
```

`renderer.py`の`_strip_dot_prefix`により、payload上のファイル名`dot-gitignore`は生成先で
`.gitignore`に変換されます（`_transform_path`）。`[[files]].path`は変換後のdest_path空間
（`.gitignore`）で指定する必要があります（`_file_strategy`の照合ロジックに合わせる）。

## 5. 失敗とロールバック

- `base`の内容を変更しないため、既存の全プロファイル・全lang選択（`--lang`省略を含む）への
  影響はありません
- `lang/typescript`は「無視されるファイルが増える」方向のみの変更で、破壊的変更はありません
- ロールバックは`git revert`で可能です

## 6. 検証

| テスト層 | 検証内容 |
| --- | --- |
| `tests/e2e/test_generate_profiles.py` | `--lang python`生成物・`--lang`省略生成物の両方で`.gitignore`に`__pycache__/`が含まれる（回帰防止）／`--lang typescript`生成物に`node_modules/`と`__pycache__/`の両方が含まれる（base継承の確認） |
| `tests/unit/test_schema.py` | `lang/typescript`の`part.toml`の`[[files]]`追加がスキーマ検証を通ること（変更不要、既存の動的globで対象に入る） |
| `just verify`（このリポジトリ） | 全チェックpass |

## 7. 未解決事項

- **`base`の`__pycache__/`除去は`starter/*`のlang非依存化が前提**: `starter/*`がPython専用
  スケルトンを無条件で出す限り、`base`の`.gitignore`から`__pycache__/`を抜くことはできません。
  この制約は`starter/*`のlang別スケルトン対応（M6+相当、issue #88のhtmx starter設計とも
  関連しうる）が進んだ時点で再評価します
- **`lang/rust`への適用**: 上記4.3節の通り、#86ブランチのrebase後に別コミットで適用します
- **将来の`lang/go`対応**: 本Issueで確立したパターン（base全文+lang固有エントリを
  `strategy="replace"`で複製）にそのまま従う想定。設計判断は不要
- **U-06との関係**: 複数lang同時指定時の`.gitignore`合成は、flake.nixの`append`戦略と同じ
  タイミング（フェーズ5）でまとめて設計する
