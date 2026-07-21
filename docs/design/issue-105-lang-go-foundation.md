---
status: proposed
proposed_at: 2026-07-21
approved_at: null
approved_by: null
implemented_at: null
related: "#105"
---

# 設計提案: lang/goのgo.modに基盤依存(godotenv)を組み込む

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

「Nix開発テンプレート改善方針」のGo「必須」は`log/slog`(標準)・`godotenv`です。
`log/slog`はGo標準ライブラリのため追加作業は不要で、`godotenv`のみが本Issueの対象です。

Issue番号#100(lang/rustのCargo.toml拡張)と同じ設計判断で、`features/logging-python`の
ような別Partのopt-in注入ではなく、`lang/go`自体のgo.modへ直接組み込みます。

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| `lang/go`の`go.mod`への`godotenv`追加、`main.go`プレースホルダーの更新 | `starter/web-api-go`等の用途別複合Part追加(#98の後続Issue) |
| 生成プロジェクトでの`go build`/`test`/`golangci-lint`の手動確認 | Python/TypeScriptの同種対応(それぞれ別Issue) |

## 3. 選択肢

| 案 | 内容 | 評価 |
| --- | --- | --- |
| A | `lang/go`のgo.mod自体に直接組み込む | ← 推奨。#100と同じ「lang/*=言語のbase」という設計と一致 |
| B | `features/foundation-go`という新規opt-in Part | 見送り。#100と同じ理由(opt-in運用は「ほぼ全員が使う」前提と矛盾) |

案Aを採用します。

## 4. 設計案

### 4.1. `go.mod`への依存追加

```text
module {{project_name}}

go 1.23

require github.com/joho/godotenv v1.5.1
```

`go mod tidy`実行時にgo.sumが生成されます(Cargo.lockと同様、テンプレートには含めず
初回ビルド時に生成、ユーザーがcommitする運用)。

### 4.2. `main.go`の更新

`godotenv`を実際にコード内で使用します。`.env`が存在しない場合もエラーにせず、
`slog`で情報ログを出すのみとします(新規生成直後は`.env`が無いのが通常状態のため)。

```go
// Generated placeholder — delete when you add real code
package main

import (
	"fmt"
	"log/slog"

	"github.com/joho/godotenv"
)

func main() {
	if err := godotenv.Load(); err != nil {
		slog.Info("no .env file found, using system environment variables")
	}
	fmt.Println("Hello, {{project_name}}!")
}
```

### 4.3. 将来の用途別複合Partとの関係

`starter/web-api-go`(#98の後続Issue)は`requires=["lang/go", ...]`かつ`go.mod`を
`strategy="replace"`で提供する想定です。#100・#102と同じresolver+plannerの仕組みにより、
`starter/web-api-go`のgo.modは「本Issueで確立したbase依存 + chi/gin等」という累積的な
スーパーセットとして書くことになります。

## 5. 失敗とロールバック

- 追加ファイルの変更のみで、他Part(`starter/*-python`等)への影響はありません
- `go build`/`go mod tidy`は初回、Go moduleプロキシへのネットワークアクセスが必要です
  (既存の`lang/rust`のcrates.ioアクセスと同じ前提)
- ロールバックは`git revert`で可能です

## 6. 検証

| テスト層 | 検証内容 |
| --- | --- |
| `tests/e2e/test_generate_profiles.py` | 生成した`go.mod`に`godotenv`が含まれること |
| 手動確認 | 生成プロジェクトで`nix develop --command go build`・`go test`・`golangci-lint run`が成功すること |
| `just verify`(このリポジトリ) | 全チェックpass |

## 7. 未解決事項

- **依存の重複**: 4.3節の通り、将来`starter/web-api-go`等がgo.modを拡張する際、
  本Issueのbase依存一覧を手動で書き写す必要があります(#100と同じトレードオフ)
- **Python/TypeScriptへの横展開**: 別Issueとします
