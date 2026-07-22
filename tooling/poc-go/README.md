---
status: draft
---

# tooling/poc-go

## 概要

Go言語によるジェネレータPoC（Proof of Concept）です。
PythonジェネレータのGo移行可否判断（Issue #112）のために作成しました。

## 責任

- Profile/PartのTOML読み込み（LOADステージ）
- Part依存解決・順序決定（RESOLVEステージ）
- 変数束縛・ファイル一覧作成（PLANステージ）
- 複数ロール生成前のpreflight検証

## 責任外

- ファイル生成（RENDER/APPLYステージ）は実装しません
- productionのentrypointへの統合はこのPoCのスコープ外です

## ディレクトリ構成

```text
tooling/poc-go/
├── cmd/generate/main.go       # CLIエントリポイント（dry-run, no files written）
├── internal/
│   ├── models/models.go       # データ型定義
│   ├── loader/loader.go       # LOAD: TOML読み込み
│   ├── loader/loader_test.go
│   ├── resolver/resolver.go   # RESOLVE: 依存解決
│   ├── resolver/resolver_test.go
│   ├── planner/planner.go     # PLAN: 変数束縛・ファイル一覧
│   ├── planner/planner_test.go
│   ├── preflight/preflight.go # --role preflight検証
│   └── preflight/preflight_test.go
├── go.mod
└── go.sum
```

## 使い方

```sh
# 単一生成（ドライラン、ファイル生成なし）
go run ./cmd/generate --name myapp --profile starter-cli --lang python

# 複数ロールのpreflight検証
go run ./cmd/generate --name myapp \
  --role backend:profile=starter-web-api,lang=python \
  --role frontend:profile=starter-cli,lang=go

# テスト
go test ./...

# フォーマット
gofmt -w .

# 静的解析
go vet ./...
```
