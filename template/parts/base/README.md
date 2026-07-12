# template/parts/base

## 1. 概要

全プロファイル共通の開発基盤（Nix flake・just・pre-commit・CI・README 骨格）を提供する base Part です。

## 2. 責任

- `part.toml` によるメタデータと依存宣言
- `payload/` 配下の生成対象ファイル群（実装済み）

## 3. 責任外

- スケール・用途・機能別のファイル（各 Part が担当）
