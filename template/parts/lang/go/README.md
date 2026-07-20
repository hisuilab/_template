# template/parts/lang/go

## 1. 概要

Go 言語環境（go / gofmt / golangci-lint）を提供する lang Part です。

## 2. 責任

- `part.toml` によるメタデータと依存宣言（requires: base, conflicts: lang/python, lang/typescript, lang/rust）
- `payload/flake.nix`: base packages + go + golangci-lint を含む devShell
- `payload/treefmt.nix`: base フォーマット設定 + gofmt
- `payload/justfile`: base レシピ + `test`（go test）+ `lint`（treefmt + golangci-lint）、`github-*` レシピ（`strategy=replace` のため base justfile の全内容を複製）
- `payload/go.mod` / `payload/main.go` / `payload/main_test.go`: `go build` / `go test` / `go vet` の実行に必要な最小マニフェストとプレースホルダー（Goのエコシステム慣習に従いリポジトリルート直下に配置。cargo と異なり `src/` を介さない）
- `payload/dot-gitignore`: base 共通内容 + Go向けビルド成果物パターン（`*.exe` 等）

## 3. 責任外

- Go ソースコードの役割別骨格（starter Part が担当。本 Part は最小プレースホルダーのみ提供）
- 複数言語構成のマージ（M6+ の append 戦略が担当）
