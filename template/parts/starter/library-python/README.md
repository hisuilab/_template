# template/parts/starter/library-python

## 1. 概要

`starter/library`のPython実装（パッケージ本体`src/{{project_name}}/__init__.py`）を提供する
複合Partです。`--lang python`が選択され、かつ`starter/library`が適用されている場合にのみ
注入されます。

## 2. 責任

- `part.toml`によるメタデータと依存宣言（requires: base, starter/library, lang/python）
- `payload/src/{{project_name}}/__init__.py`: パッケージ本体

## 3. 責任外

- lang非依存の骨格（`starter/library`が担当）
- Python以外の言語向け実装（`starter/library-typescript`等、将来追加予定の複合Partが担当）
