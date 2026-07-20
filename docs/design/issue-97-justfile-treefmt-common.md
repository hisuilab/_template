---
status: implemented
proposed_at: 2026-07-20
approved_at: 2026-07-20
approved_by: PM
implemented_at: 2026-07-20
related: "#97"
---

# 設計提案: justfile/treefmt.nixのlang間重複をimport化する

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

`template/parts/lang/{python,typescript,rust,go}/payload/`の`justfile`(4ファイル合計約
457行)・`treefmt.nix`(4ファイル合計約164行)は、実質的な差分が数行(lint/testレシピ、
formatter有効化1行)にもかかわらずほぼ全文をコピーしています。セッション内で`base`の
justfile(`init`にdirenv allow追加)がlang側3ファイルへ反映されずに一時的にドリフトした
実例があり、保守コストとして顕在化しました。

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| `base`が`common.just`・`treefmt-base.nix`を提供し、4つの`lang/*`がそれを利用する形へ縮小 | `flake.nix`の共通化(可読性とのトレードオフがあり別途PM判断が必要) |
| 既存4 lang Partの`justfile`・`treefmt.nix`の書き換え | `.gitignore`の`append`戦略導入(ジェネレータへの新戦略追加が必要で規模が異なる、Issue #97の対象外) |

## 3. 選択肢

事前に2つの技術を隔離環境で実機検証しました。

| 技術 | 検証内容 | 結果 |
| --- | --- | --- |
| `just import` + `set allow-duplicate-recipes := true` | `common.just`に`foo`・`bar`を定義し、importする側の`justfile`で`foo`のみ再定義。`just foo`が再定義側、`just bar`がcommon側の出力になるか確認 | ✓ 動作確認済み。再定義したレシピは importする側が優先される |
| treefmt-nixの`imports`合成 | `treefmt-base.nix`(nixfmt)を`imports`する`treefmt.nix`(shfmt追加)で`nix flake check`・`nix build .#formatter`を実行し、生成された`treefmt.toml`に両方の`[formatter.*]`が含まれるか確認 | ✓ 動作確認済み。`[formatter.nixfmt]`・`[formatter.shfmt]`が両方生成された |

| 案 | 内容 | 評価 |
| --- | --- | --- |
| A | `base`が`common.just`・`treefmt-base.nix`を提供し、`lang/*`はimport+差分のみを書く | ← 推奨。実機検証済みの手法のみを使い、ジェネレータ(`tooling/generator/`)側の変更が一切不要。`common.just`・`treefmt-base.nix`は`base`の`file_rules`宣言なしデフォルト(`strategy="error"`)のまま新規ファイルとして追加するだけで、既存の衝突検出の仕組みにも影響しない |
| B | ジェネレータに真の`"append"`戦略を実装し、justfile/treefmt.nixもgitignoreと同じ仕組みで合成する | 見送り。justfileはテキスト行の単純結合では`verify: lint check-docs ...`のような他レシピへの参照を含む集約レシピが成立しない(依存関係の再計算が必要)。treefmt.nixもNix式であり単純な行結合が意味を持たない。いずれも案Aの言語ネイティブな合成機構の方が正確 |
| C | 現状維持 | 見送り。重複と将来のドリフトリスクを許容し続ける |

案Aを採用します。

## 4. 設計案

### 4.1. `base`に`common.just`を追加

`template/parts/base/payload/common.just`として、現行`justfile`の共通部分
(`format`・`check-docs`・`check-readme`・`check-status`・`check-encoding`・`inject`・
`init`・`github-*`)を切り出します。`versions`はlang固有の行を含むため`common.just`には
含めず、各lang justfileが独自に定義します(既存のまま)。

`base`自身の`justfile`(lang未指定時のフォールバック)は次の形になります。

```just
set allow-duplicate-recipes := true

import 'common.just'

verify: lint check-docs check-readme check-status check-encoding

# show versions of all development tools
versions:
    @echo "just:    $(just --version)"
    @echo "treefmt: $(treefmt --version 2>&1 | head -1)"
    @echo "rumdl:   $(rumdl --version 2>&1 | head -1)"
    @echo "git:     $(git --version)"
```

`lint`・`format`は`common.just`側に定義し(`treefmt`のみを呼ぶ既存内容のまま)、`base`は
再定義しません。

### 4.2. 各`lang/*`の`justfile`

`lang/rust`を例にすると次の形へ縮小します(117行 → 約20行)。

```just
set allow-duplicate-recipes := true

import 'common.just'

# requires: treefmt, cargo, clippy
lint:
    treefmt --fail-on-change
    cargo clippy --all-targets --all-features -- -D warnings

# requires: cargo
test:
    cargo test

verify: lint check-docs check-readme check-status check-encoding test

# show versions of all development tools
versions:
    @echo "rustc:   $(rustc --version)"
    @echo "cargo:   $(cargo --version)"
    @echo "clippy:  $(cargo clippy --version)"
    @echo "just:    $(just --version)"
    @echo "treefmt: $(treefmt --version 2>&1 | head -1)"
    @echo "rumdl:   $(rumdl --version 2>&1 | head -1)"
    @echo "git:     $(git --version)"
```

`common.just`が提供する`format`・`check-docs`・`check-readme`・`check-status`・
`check-encoding`・`inject`・`init`・`github-*`はそのまま継承され、`lint`・`test`・
`verify`・`versions`のみをlang側で上書きします。

`part.toml`の`[[files]]`に`common.just`は含めません(`base`が`strategy`未宣言のデフォルト
`"error"`で提供し、`lang/*`はこのファイルを一切触らないため、衝突が起こり得ません)。

### 4.3. `base`に`treefmt-base.nix`を追加

`template/parts/base/payload/treefmt-base.nix`として、現行`treefmt.nix`の共通部分
(nixfmt・taplo・prettier・shellcheck・shfmt)を切り出します。`base`自身の`treefmt.nix`は
次の形になります。

```nix
{ ... }:
{
  projectRootFile = "flake.nix";
  imports = [ ./treefmt-base.nix ];
}
```

### 4.4. 各`lang/*`の`treefmt.nix`

`lang/rust`を例にすると次の形へ縮小します(39行 → 約6行)。

```nix
{ ... }:
{
  projectRootFile = "flake.nix";
  imports = [ ./treefmt-base.nix ];
  programs.rustfmt.enable = true;
}
```

`lang/typescript`は`biome`の`includes`設定など追加のカスタマイズがあるため、他langより
やや長くなりますが、`nixfmt`・`taplo`・`prettier`・`shellcheck`・`shfmt`の重複は同様に
解消されます。

## 5. 失敗とロールバック

- `common.just`・`treefmt-base.nix`は新規ファイルで、既存の生成結果(レシピの実行結果・
  formatter設定)は変更しません。回帰は「レシピ一覧・formatter設定が現状と完全に一致する
  こと」をe2e/手動確認で担保します
- `set allow-duplicate-recipes := true`は`just`の標準機能であり、Nix以外の追加依存は
  発生しません
- ロールバックは`git revert`で可能です

## 6. 検証

| テスト層 | 検証内容 |
| --- | --- |
| `tests/e2e/test_generate_profiles.py` | 生成された`justfile`・`treefmt.nix`に既存の検証(`"biome" in justfile`等)が引き続き通ること(importの結果でも文字列としては最終的に同じ設定が有効になる) |
| 手動確認 | `--lang python`/`typescript`/`rust`/`go`それぞれで生成し、`nix develop --command just verify`・`nix develop --command just --list`(レシピ一覧が変わらないこと)・`nix develop --command treefmt --fail-on-change`(formatter適用結果が変わらないこと)を確認 |
| `just verify`(このリポジトリ) | 全チェックpass |

## 7. 未解決事項

- **`flake.nix`の共通化**: Nixの`import ./flake-lib.nix { extraPackages = ...; }`で
  技術的には可能だが、生成後プロジェクトの`flake.nix`の可読性(devShell定義が別ファイルに
  分散する)とのトレードオフがあるため、本Issueでは対象外とし別途PM判断を仰ぐ
- **`.gitignore`の`append`戦略**: ジェネレータへの新戦略追加が必要で本Issueとは規模が
  異なるため別Issueとする
