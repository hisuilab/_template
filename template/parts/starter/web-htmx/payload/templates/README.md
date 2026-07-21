# templates

## 1. 概要

サーバーサイドレンダリング用のテンプレートを置くディレクトリです。

## 2. 責任

- lang非依存の骨格(このディレクトリ自体)

## 3. 責任外

- 言語別のテンプレート実装(`layout.html`・`index.html`等。`--lang rust`選択時は
  `starter/web-htmx-rust`が提供。`--lang`省略時や対応する複合Partが無い言語では
  生成されない)
