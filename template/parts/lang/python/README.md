# template/parts/lang/python

## 1. 概要

Python 言語環境（python3 / uv / ruff / pytest）を提供する lang Part です。

## 2. 責任

- `part.toml` によるメタデータと依存宣言（requires: base, conflicts: lang/typescript）
- `payload/flake.nix`: base packages + python3 / uv / ruff / pytest を含む devShell
- `payload/treefmt.nix`: base フォーマット設定 + ruff
- `payload/justfile`: base レシピ + `test`（pytest）と `verify` への追加
- `payload/tests/test_placeholder.py`: pytest が exit 5 を返さないためのスタブ

## 3. 責任外

- Python ソースコードの骨格（purpose Part が担当）
- 複数言語構成のマージ（M6+ の append 戦略が担当）
