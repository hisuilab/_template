# template/parts/starter/cli-python

## 1. 概要

`starter/cli`のPython実装（エントリポイント`src/main.py`）を提供する複合Partです。
`--lang python`が選択され、かつ`starter/cli`が適用されている場合にのみ注入されます。

## 2. 責任

- `part.toml`によるメタデータと依存宣言（requires: base, starter/cli, lang/python）
- `payload/src/main.py`: CLIエントリポイント

## 3. 責任外

- lang非依存の骨格（`starter/cli`が担当）
- Python以外の言語向け実装（`starter/cli-typescript`等、将来追加予定の複合Partが担当）
