# template/parts/lang/typescript

## 1. 概要

TypeScript 言語環境（nodejs / typescript）を提供する lang Part です。

## 2. 責任

- `part.toml` によるメタデータと依存宣言（requires: base, conflicts: lang/python）
- `payload/flake.nix`: base packages + nodejs を含む devShell
- `payload/treefmt.nix`: base フォーマット設定 + prettier（.ts / .tsx）
- `payload/justfile`: base レシピ + `type-check`（npx tsc）

## 3. 責任外

- TypeScript ソースコードの骨格（M6+ の purpose Part が担当）
- 複数言語構成のマージ（M6+ の append 戦略が担当）
