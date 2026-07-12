# template/parts/features/logging-typescript

## 1. 概要

Node.js 組み込み `console` を使ったロギング基盤を追加する features/logging-typescript Part です。`src/logger.ts` の `getLogger(name)` ヘルパーを提供します。外部 npm パッケージへの依存はありません。

## 2. 責任

- `part.toml` によるメタデータと依存宣言
- `payload/src/logger.ts`: `getLogger(name: string)` ヘルパー（`LOG_LEVEL` 環境変数で制御）

## 3. 責任外

- Python ロギング（features/logging-python が担当）
- 外部ロギングライブラリのインストール（pino / winston 等）
