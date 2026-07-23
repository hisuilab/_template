# template/parts/starter/web-api-rust

## 1. 概要

`starter/web-api`のRust実装(axum + tokio + reqwestによる最小Webサーバー)を提供する
複合Partです。`--lang rust`が選択され、かつ`starter/web-api`が適用されている場合にのみ
注入されます。

## 2. 責任

- `part.toml`によるメタデータと依存宣言(requires: base, starter/web-api, lang/rust)
- `payload/Cargo.toml`: web-api固有依存（axum/tokio/reqwest）の差分断片。`append`戦略で
  `lang/rust`の基盤依存断片と結合され、生成物に全依存が含まれます（issue #129）
- `payload/src/main.rs`: axum最小Webサーバー(`/health`エンドポイント)

## 3. 責任外

- lang非依存の骨格(`starter/web-api`が担当)
- Rust以外の言語向け実装(`starter/web-api-typescript`等、将来追加予定の複合Partが担当)
- HTMX/Askama/Pico CSS等のview層(#88が担当)
