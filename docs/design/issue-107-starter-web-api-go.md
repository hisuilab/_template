---
status: proposed
proposed_at: 2026-07-21
approved_at: null
approved_by: null
implemented_at: null
related: "#107"
---

# 設計提案: starter/web-api-go複合Partを追加する

状態はfrontmatter(`status`・`proposed_at`・`approved_at`・`approved_by`・`implemented_at`・
`related`)が正本です。

## 目次

- [1. 問題](#1-問題)
- [2. 対象範囲](#2-対象範囲)
- [3. 選択肢](#3-選択肢)
- [4. 設計案](#4-設計案)
- [5. 失敗とロールバック](#5-失敗とロールバック)
- [6. 検証](#6-検証)
- [7. 未解決事項](#7-未解決事項)

## 1. 問題

「Nix開発テンプレート改善方針」のGo Web API用途(chi または gin)を、#91で確立した
`starter/<purpose>-<lang>`複合Partパターンで実現します。#105で`lang/go`のgo.modに
基盤依存(godotenv)を組み込んだので、本Issueはその上にWeb API向け依存を積みます。
Issue番号#102(starter/web-api-rust)と同型のパターンです。

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| `template/parts/starter/web-api-go/`(part.toml + payload/)の追加 | ルーティング構成の作り込み(用途別Partのプレースホルダーとしては最小限に留める) |
| `go.mod`(#105の基盤依存+chi)・`main.go`(chi Webサーバー) | HTMX等のview層(必要になれば別Issue) |

## 3. 選択肢

| 案 | 内容 | 評価 |
| --- | --- | --- |
| A | `chi`(net/http標準ライブラリ互換の軽量ルーター)を採用 | ← 推奨。ginより薄く、「baseは必要最小限」という既存の設計思想(#100・#105のfoundation依存の絞り込み方針)と一貫する。`net/http`の`http.Handler`をそのまま使えるため学習コストが低い |
| B | `gin`(独自のContext型を持つ高機能フレームワーク) | 見送り。標準ライブラリからの乖離が大きく、Goの「標準ライブラリで足りることは標準ライブラリで」という慣習からも外れる |

案Aを採用します。

## 4. 設計案

### 4.1. `part.toml`

```toml
[part]
id = "starter/web-api-go"
layer = "starter"
summary = "starter/web-api の Go 実装（chi）"
requires = ["base", "starter/web-api", "lang/go"]
conflicts = []

[placeholders]
required = ["project_name"]

[[files]]
path = "go.mod"
strategy = "replace"

[[files]]
path = "main.go"
strategy = "replace"
```

`lang/go`も`go.mod`・`main.go`を`strategy="replace"`で提供しますが、resolverが
`requires`(`lang/go`が`starter/web-api-go`の依存)に基づき`lang/go`を先に適用するため、
plannerの「後発の`replace`が勝つ」規則により`starter/web-api-go`側の内容が最終的に
採用されます(#100・#102で確認済みの仕組み、新しい合成機構は不要)。

### 4.2. `go.mod`(累積的なスーパーセット)

`lang/go`の基盤依存(#105: godotenv)を含んだ上でchiを追加します。

```text
module {{project_name}}

go 1.23

require (
	github.com/go-chi/chi/v5 v5.1.0
	github.com/joho/godotenv v1.5.1
)
```

正確なバージョンは実装時の`go mod tidy`で確認・調整します(#87のgo.modバージョン floor
検証と同じ手順)。

### 4.3. `main.go`(chi最小サーバー)

```go
// Generated placeholder — delete when you add real code
package main

import (
	"log/slog"
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/joho/godotenv"
)

func main() {
	if err := godotenv.Load(); err != nil {
		slog.Info("no .env file found, using system environment variables")
	}

	r := chi.NewRouter()
	r.Get("/health", func(w http.ResponseWriter, _ *http.Request) {
		w.Write([]byte("ok"))
	})

	slog.Info("listening", "addr", ":3000")
	if err := http.ListenAndServe(":3000", r); err != nil {
		slog.Error("server error", "error", err)
	}
}
```

### 4.4. `starter/web-api`骨格との共存

`starter/web-api`(骨格Part)が提供する`src/README.md`・`src/routes/README.md`は、
`starter/web-api-go`が`main.go`をリポジトリルート直下に置く(#87で確立したGoの配置慣習)
ため衝突なく共存します(#102で確認済みのパターン)。

## 5. 失敗とロールバック

- 追加Partのみで、既存プロファイルへの影響はありません
- `--lang go`+`starter-cli`のような組み合わせでは`starter/web-api-go`は注入されず、
  `lang/go`単体のプレースホルダーが引き続き使われます(回帰なし)
- ロールバックは`git revert`で可能です

## 6. 検証

| テスト層 | 検証内容 |
| --- | --- |
| `tests/e2e/test_generate_profiles.py` | `--lang go`+`starter-web-api`で生成した`go.mod`にchiが含まれること、`main.go`が存在すること |
| 手動確認 | 生成プロジェクトで`go build`/`go test`/`golangci-lint run`が成功すること。実際にサーバーを起動し`/health`エンドポイントへのリクエストが成功すること |
| `just verify`(このリポジトリ) | 全チェックpass |

## 7. 未解決事項

- **`starter/cli-go`・`starter/library-go`**: 本Issueと同型のパターンで、必要になった
  時点で別Issueとして追加します
- **依存の重複**: 将来他の用途別Partを追加する際、本Issueのbase依存一覧を手動で
  書き写す必要があります(#100・#102と同じトレードオフ)
