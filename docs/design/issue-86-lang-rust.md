---
status: implemented
proposed_at: 2026-07-20
approved_at: 2026-07-20
approved_by: PM
implemented_at: 2026-07-20
related: "#86"
---

# 設計提案: lang/rust Part を追加する

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

`template/parts/lang/`は`python`・`typescript`のみで、Rust環境を`--lang rust`で生成できません。
`_available_langs()`(`tooling/generator/cli.py`)は`template/parts/lang/`配下を動的スキャンする
ため、CLI側のコード変更なしに`lang/rust`ディレクトリを追加すれば`--lang rust`が有効になります。
本提案はNix flakeへのRustツールチェイン組み込み方針と、`just verify`を生成直後からグリーンに
保つための最小`src/`スタブの要否を確定します。

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| `template/parts/lang/rust/`（part.toml + payload/）の追加 | `starter/*`のRust版スケルトン（役割別`src/`。将来のTypeScript同様M6+相当） |
| 既存`lang/python`・`lang/typescript`の`conflicts`への`lang/rust`追加 | 複数lang同時指定・flake.nixの`append`マージ戦略（U-06、フェーズ5） |
| e2eテストへの`--lang rust`ケース追加 | rust-overlay等の外部flake inputによるRustバージョン固定 |

## 3. 選択肢

Rustツールチェインの供給元について検討しました。

| 案 | 内容 | 評価 |
| --- | --- | --- |
| A | nixpkgs標準パッケージ（`rustc`/`cargo`/`clippy`/`rustfmt`）を直接使用 | ← 推奨。既存`lang/python`（`python3`/`uv`/`ruff`）・`lang/typescript`（`nodejs`/`biome`）と同じく、新規flake inputを追加せずnixpkgsチャンネル（`nixos-25.11`）だけでバージョンを固定する既存パターンと一貫する。バージョンはnixpkgsチャンネル追従（rustupのような任意バージョン切り替えは不可）が制約だが、python3/nodejsも同じ制約を既に受け入れている |
| B | `oxalica/rust-overlay`または`nix-community/fenix`を追加flake inputとして導入し、`rust-toolchain.toml`で厳密なバージョン指定 | 見送り。新規依存の追加は`policy.md`により事前承認が必要かつ保守コスト増。現時点でRustの特定マイナーバージョン固定が要件化されていないため過剰 |
| C | `rustup`をdevShellに含め、シェル起動時に`rustup toolchain install`を実行 | 見送り。Nixストア外への可変ダウンロードが発生し再現性が失われる（Nixの目的に反する） |

案Aを採用します。

## 4. 設計案

### 4.1. `part.toml`

```toml
[part]
id = "lang/rust"
layer = "lang"
summary = "Rust言語環境（rustc / cargo / clippy / rustfmt）"
requires = ["base"]
conflicts = ["lang/python", "lang/typescript"]

[placeholders]
required = ["project_name"]

[[files]]
path = "flake.nix"
strategy = "replace"

[[files]]
path = "treefmt.nix"
strategy = "replace"

[[files]]
path = "justfile"
strategy = "replace"

[[files]]
path = "Cargo.toml"
strategy = "replace"

[[files]]
path = "src/main.rs"
strategy = "replace"
```

### 4.2. `flake.nix`（base差分）

`devShells.default.packages`に追加:

```nix
pkgs.cargo
pkgs.clippy
pkgs.rustc
pkgs.rustfmt
```

`cargo`だけでは`cargo clippy`は動かない（`clippy-driver`は別パッケージ）ため`pkgs.clippy`を
明示的に追加します。`rustfmt`はtreefmtからも使われますが、`just versions`での直接参照
（python/typescriptの`pkgs.ruff`・`pkgs.biome`と同じ扱い）のためdevShellにも明示します。

### 4.3. `treefmt.nix`（base差分）

```nix
programs.rustfmt.enable = true;
```

treefmt-nixが標準で提供するrustfmtモジュールを使用します（`programs.ruff`・`programs.biome`と
同型）。

### 4.4. `justfile`（base差分）

```just
# requires: cargo, clippy
lint:
    treefmt --fail-on-change
    cargo clippy --all-targets --all-features -- -D warnings

# requires: cargo
test:
    cargo test

verify: lint check-docs check-readme check-status check-encoding test
```

`just versions`に`rustc --version`・`cargo --version`・`cargo clippy --version`を追加します。

### 4.5. 最小`src/`スタブの必要性

pytestは`tests/`ディレクトリのみで実行できますが、`cargo test`・`cargo clippy`・`cargo build`は
`Cargo.toml`（マニフェスト）が無いと即エラー終了します。`starter/*`は現状Python専用で
Rust版が無い（本Issueの対象外）ため、`lang/rust`単体で`just verify`をグリーンに保つには、
`lang` Part自身が最小限の`Cargo.toml`・`src/main.rs`を提供する必要があります。

```toml
# Cargo.toml
[package]
name = "{{project_name}}"
version = "0.1.0"
edition = "2021"
```

```rust
// src/main.rs — Generated placeholder — delete when you add real code
fn main() {
    println!("Hello, {{project_name}}!");
}

#[cfg(test)]
mod tests {
    #[test]
    fn placeholder() {}
}
```

Rustの慣習に従い、ユニットテストは`src/main.rs`内の`#[cfg(test)] mod tests`に配置します
（`lang/python`の`tests/test_placeholder.py`と同じ役割のプレースホルダー）。

> [!NOTE]
> Cargo package名にはハイフンを含むプロジェクト名も使用可能です（`_validate_name`が許可する
> `[a-zA-Z0-9_-]+`はCargoの命名規則と両立します）。

### 4.6. 既存Partへの影響

`lang/python`・`lang/typescript`の`part.toml`の`conflicts`に`lang/rust`を追加します（ペア方式の
双方向管理）。

## 5. 失敗とロールバック

- 追加ファイルのみで既存生成物（python/typescriptプロファイル）への影響はありません
- `conflicts`追加は既存挙動を変えません（新しい組み合わせを禁止する側の変更のみ）
- ロールバックは`git revert`で可能です

## 6. 検証

| テスト層 | 検証内容 |
| --- | --- |
| `tests/unit/test_schema.py` | `lang/rust`のpart.tomlがスキーマ検証を通ること |
| `tests/e2e/test_generate_profiles.py` | `--lang rust`で生成した`flake.nix`に`rustc`/`cargo`が含まれること |
| 手動確認 | 生成プロジェクトで`nix develop --command cargo --version`・`nix develop --command just verify`がグリーン |
| `just verify`（このリポジトリ） | 全チェックpass |

## 7. 未解決事項

- **RustのStarter Part**: `starter/*`のRust版役割別スケルトン（`src/lib.rs`分割等）はM6+相当。
  本Issueでは`lang/rust`が提供する最小`src/main.rs`のみで代替します
- **バージョン固定の柔軟性**: rust-overlay等による厳密バージョン指定は、要件化された時点で
  改めて検討します（U-06関連の複数lang対応と合わせてフェーズ5で再評価）
