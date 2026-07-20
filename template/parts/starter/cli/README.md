# template/parts/starter/cli

## 1. 概要

CLI ツール向けの `src/` 骨格（lang 非依存）を提供する starter/cli Part です。`--lang` 省略時
はこの骨格のみが生成されます。

## 2. 責任

- `part.toml` によるメタデータと依存宣言
- `payload/` 配下の生成対象ファイル群（`src/README.md` のみ、lang 非依存）

## 3. 責任外

- Web API・ライブラリ向けの骨格（他 starter Part が担当）
- 言語別のエントリポイント実装（`starter/cli-python` 等、lang 別の複合 Part が担当）
