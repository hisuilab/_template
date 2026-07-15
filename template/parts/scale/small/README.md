# template/parts/scale/small

## 1. 概要

`docs/` ディレクトリ骨格（`draft/`・`requirements/`・`architecture/`・`design/`・`decisions/`・`progress/` の README）を提供する scale/small Part です。

## 2. 責任

- `part.toml` によるメタデータと依存宣言
- `payload/` 配下の生成対象ファイル群（`docs/` 直下 + 6 サブディレクトリの README）

## 3. 責任外

- 具体的な設計・要件ドキュメントの内容（各専用ファイルが担当）
- `docs/milestones/` など上位スケールが追加するディレクトリ（scale/medium 以降が担当）
