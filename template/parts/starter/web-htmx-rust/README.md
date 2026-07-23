# template/parts/starter/web-htmx-rust

## 1. 概要

`starter/web-htmx`のRust実装(axum + askama + HTMX + Pico CSSによる最小サーバーレンダリング
アプリ)を提供する複合Partです。`--lang rust`が選択され、かつ`starter/web-htmx`が適用されて
いる場合にのみ注入されます。

## 2. 責任

- `part.toml`によるメタデータと依存宣言(requires: base, starter/web-htmx, lang/rust)
- `payload/Cargo.toml`: htmx固有依存（askama/askama_axum/axum/reqwest/tokio/tower-http）の
  差分断片。`append`戦略で`lang/rust`の基盤依存断片と結合され、生成物に全依存が含まれます
  （issue #129）
- `payload/src/main.rs`: axum最小サーバー(`/`・`/message`エンドポイント、HTMXの部分
  レンダリングを実演)
- `payload/templates/layout.html`: HTMX・Pico CSSをCDN経由で読み込む共通レイアウト
- `payload/templates/index.html`・`message.html`: Askamaテンプレート

## 3. 責任外

- lang非依存の骨格(`starter/web-htmx`が担当)
- Rust以外の言語向け実装(`starter/web-htmx-typescript`等、将来追加予定の複合Partが担当)
- 静的アセットのvendoring(CDN経由のため対象外。設計提案7節の未解決事項)
