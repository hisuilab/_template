# template/parts/lang/python

## 1. 概要

Python 言語環境（python3 / uv / ruff / pytest）を提供する lang Part です。

## 2. 責任

- `part.toml` によるメタデータと依存宣言（requires: base, conflicts: lang/typescript, lang/rust）
- `payload/flake.nix`: base packages + python3 / uv / ruff / pytest を含む devShell
- `payload/treefmt.nix`: `treefmt-base.nix`を`imports`+ruff（`strategy=replace`のためファイル自体は複製するが、内容はbase共通部分をimportで参照する）
- `payload/justfile`: `common.just`を`import`+`test`（pytest）と`verify`への追加（`github-*`等の共通レシピは`common.just`側にあり複製しない。issue #97）
- `payload/tests/test_placeholder.py`: pytest が exit 5 を返さないためのスタブ
- `payload/dot-gitignore`: base 共通内容 + `__pycache__/` / `*.pyc`

## 3. 責任外

- Python ソースコードの骨格（starter Part が担当）
- 複数言語構成のマージ（M6+ の append 戦略が担当）
