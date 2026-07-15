# template/parts/architecture/layered

## 1. 概要

レイヤードアーキテクチャ向けのディレクトリ構成（interface / application / domain / infrastructure の 4 層）を提供する architecture/layered Part です。

## 2. 責任

- `part.toml` によるメタデータと依存宣言
- `src/` 4 層の README（責任・責任外）
- `tests/unit/`・`tests/integration/` の README
- `docs/architecture/dependencies.md`（依存関係図スタブ）

## 3. 責任外

- ドメイン設計ドキュメント（`architecture/ddd` が担当）
- ソースコードの実装（プロジェクト固有）
- `docs/` の基本骨格（`scale/small` が担当）
