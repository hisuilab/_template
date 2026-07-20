# template/parts/lang/rust

## 1. 概要

Rust 言語環境（rustc / cargo / clippy / rustfmt）を提供する lang Part です。

## 2. 責任

- `part.toml` によるメタデータと依存宣言（requires: base, conflicts: lang/python, lang/typescript）
- `payload/flake.nix`: base packages + rustc + cargo + clippy + rustfmt を含む devShell
- `payload/treefmt.nix`: `treefmt-base.nix`を`imports`+rustfmt（.rs）
- `payload/justfile`: `common.just`を`import`+`test`（cargo test）+`lint`（treefmt + cargo clippy）+`verify`（`github-*`等の共通レシピは`common.just`側にあり複製しない。issue #97）
- `payload/Cargo.toml` / `payload/src/main.rs`: `cargo test` / `cargo clippy` / `cargo build` の実行に必要な最小マニフェストとプレースホルダー（pytest と異なりマニフェスト無しでは動作しないため）
- `payload/dot-gitignore`: base 共通内容 + `target/`

## 3. 責任外

- Rust ソースコードの役割別骨格（starter Part が担当。本 Part は最小プレースホルダーのみ提供）
- 複数言語構成のマージ（M6+ の append 戦略が担当）
