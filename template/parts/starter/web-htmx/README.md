# template/parts/starter/web-htmx

## 1. 概要

HTMX(サーバーレンダリング)サービス向けの`src`骨格(lang非依存)を提供するstarter Partです。
`--lang`省略時はこの骨格のみが生成されます。

## 2. 責任

- `part.toml`によるメタデータと依存宣言
- `payload/`配下の生成対象ファイル群(`templates/README.md`・`static/README.md`、lang非依存)

## 3. 責任外

- CLI・Web API・ライブラリ向けの骨格(他starter Partが担当)
- 言語別のサーバー実装(`starter/web-htmx-rust`等、lang別の複合Partが担当)
