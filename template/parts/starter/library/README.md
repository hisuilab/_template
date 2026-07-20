# template/parts/starter/library

## 1. 概要

ライブラリ・SDK 向けの `src/` 骨格（lang 非依存、パッケージディレクトリ構成・`CHANGELOG.md`）を
提供する starter/library Part です。`--lang` 省略時はこの骨格のみが生成されます。

## 2. 責任

- `part.toml` によるメタデータと依存宣言
- `payload/` 配下の生成対象ファイル群（`src/README.md`・`src/{{project_name}}/README.md`・
  `CHANGELOG.md`、lang 非依存）

## 3. 責任外

- CLI・Web API 向けの骨格（他 starter Part が担当）
- 言語別のパッケージ実装（`starter/library-python` 等、lang 別の複合 Part が担当）
