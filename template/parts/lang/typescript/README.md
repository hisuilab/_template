# template/parts/lang/typescript

## 1. 概要

TypeScript 言語環境（nodejs / biome）を提供する lang Part です。

## 2. 責任

- `part.toml` によるメタデータと依存宣言（requires: base, conflicts: lang/python）
- `payload/flake.nix`: base packages + nodejs + biome を含む devShell
- `payload/treefmt.nix`: `treefmt-base.nix`を`imports`+biome（.ts / .tsx）
- `payload/justfile`: `common.just`を`import`+`type-check`（npx tsc）+`lint`（treefmt + biome lint）+`verify`（`github-*`等の共通レシピは`common.just`側にあり複製しない。issue #97）
- `payload/package.json`: TypeScript 用途別 Part が共有する npm scripts と devDependencies
- `payload/dot-gitignore`: base 共通内容 + `node_modules/`

## 3. 責任外

- TypeScript ソースコードの骨格（starter Part が担当）
- 複数言語構成のマージ（M6+ の append 戦略が担当）
