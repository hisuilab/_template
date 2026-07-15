# template/parts/scale/large

## 1. 概要

`scale/medium` が提供するドキュメント群に、大規模プロジェクト固有のファイル（制約・観測性・スケーラビリティ・マイルストーン管理・リリース記録・ロードマップ）を追加する scale/large Part です。

## 2. 責任

- `part.toml` によるメタデータと依存宣言
- `payload/` 配下の生成対象ファイル群（architecture 拡張・milestones・releases・roadmap）

## 3. 責任外

- `docs/` 基本骨格（`scale/small` が担当）
- 要件・設計の基本ファイル群（`scale/medium` が担当）
- アーキテクチャパターン固有のドキュメント（`architecture/*` が担当）
