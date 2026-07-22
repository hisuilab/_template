# template/parts/starter/web-api-python

## 1. 概要

`starter/web-api`のPython実装（FastAPI アプリケーション本体`src/app.py`）を提供する複合Partです。
`--lang python`が選択され、かつ`starter/web-api`が適用されている場合にのみ注入されます。

## 2. 責任

- `part.toml`によるメタデータと依存宣言（requires: base, starter/web-api, lang/python）
- `payload/pyproject.toml`: FastAPI / httpx / python-dotenv / uvicorn のランタイム依存
- `payload/src/app.py`: `/health`を持つ最小FastAPIアプリケーション本体

## 3. 責任外

- lang非依存の骨格（`starter/web-api`が担当）
- Python以外の言語向け実装（`starter/web-api-typescript`等、将来追加予定の複合Partが担当）
