# src

## 1. 概要

Web API アプリケーションのソースコードを置くディレクトリです。

## 2. 責任

- `routes/`: ルーティング定義（lang 非依存の骨格）

## 3. 責任外

- テストコード（`tests/` が担当）
- 言語別のアプリケーション実装（`app.py` 等。`--lang python` 選択時は `starter/web-api-python`
  が `app.py` を提供。`--lang` 省略時や対応する複合 Part が無い言語では生成されない）
