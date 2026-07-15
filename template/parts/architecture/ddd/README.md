# template/parts/architecture/ddd

## 1. 概要

ドメイン駆動設計（DDD）向けのディレクトリ構成を提供する architecture/ddd Part です。`docs/domain/` ドメイン設計ドキュメント、`src/` 4 層、`tests/` 3 層を追加します。

## 2. 責任

- `part.toml` によるメタデータと依存宣言
- `docs/domain/`（glossary・model/・rules/）のドメイン設計ドキュメント
- `src/` 4 層の README（interface / application / domain / infrastructure）
- `tests/` 3 層の README（domain / application / integration）
- `docs/architecture/dependencies.md`（依存関係図スタブ）

## 3. 責任外

- `docs/` の基本骨格（`scale/small` が担当）
- レイヤードアーキテクチャ構成（`architecture/layered` が担当）
- ソースコードの実装（プロジェクト固有）
