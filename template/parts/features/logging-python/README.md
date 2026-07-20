# template/parts/features/logging-python

## 1. 概要

Python stdlib logging を使ったロギング基盤を追加する features/logging-python Part です。`src/logger.py` の `get_logger(name)` ヘルパーを提供します。

## 2. 責任

- `part.toml` によるメタデータと依存宣言（requires: base, lang/python。`.py`ファイルを
  同梱するため`lang/python`の`.gitignore`(`__pycache__/`無視)を前提とする）
- `payload/src/logger.py`: `get_logger(name: str) -> logging.Logger` ヘルパー

## 3. 責任外

- TypeScript ロギング（features/logging-typescript が担当）
- ログレベルの動的変更・外部ライブラリ依存（stdlib のみ）
