# template/parts/scale/medium

## 1. 概要

`scale/small` が提供する `docs/` 骨格に、要件・アーキテクチャ・設計の具体ファイル群を追加する scale/medium Part です。

## 2. 責任

- `part.toml` によるメタデータと依存宣言
- `payload/` 配下の生成対象ファイル群（要件・アーキテクチャ・設計・進捗・用語集）
- `docs/design/` 配下に機能・インターフェース・永続化・ユースケースのサブディレクトリ README を追加

## 3. 責任外

- `docs/` の基本骨格（`scale/small` が担当）
- 高度なドメイン駆動設計ドキュメント（`scale/large` または `architecture/ddd` が担当）
