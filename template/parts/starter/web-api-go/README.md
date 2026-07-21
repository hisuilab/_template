# template/parts/starter/web-api-go

## 1. 概要

`starter/web-api`のGo実装(chiによる最小Webサーバー)を提供する複合Partです。
`--lang go`が選択され、かつ`starter/web-api`が適用されている場合にのみ注入されます。

## 2. 責任

- `part.toml`によるメタデータと依存宣言(requires: base, starter/web-api, lang/go)
- `payload/go.mod`: `lang/go`の基盤依存(issue #105)を含む累積的なスーパーセット + chi
- `payload/main.go`: chi最小Webサーバー(`/health`エンドポイント)
- `payload/main_test.go`: `/health`ハンドラーの`httptest`ベースのテスト

## 3. 責任外

- lang非依存の骨格(`starter/web-api`が担当)
- Go以外の言語向け実装(`starter/web-api-typescript`等、将来追加予定の複合Partが担当)
- HTMX/Askama/Pico CSS等のview層(必要になれば別Issue)
