# template/parts/starter/web-api

## 1. 概要

Web API サービス向けの `src/` 骨格（lang 非依存、`routes/` 含む）を提供する starter/web-api
Part です。`--lang` 省略時はこの骨格のみが生成されます。

## 2. 責任

- `part.toml` によるメタデータと依存宣言
- `payload/` 配下の生成対象ファイル群（`src/README.md`・`src/routes/README.md`、lang 非依存）

## 3. 責任外

- CLI・ライブラリ向けの骨格（他 starter Part が担当）
- 言語別のアプリケーション実装（`starter/web-api-python` 等、lang 別の複合 Part が担当）
