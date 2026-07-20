---
status: proposed
proposed_at: 2026-07-20
approved_at: null
approved_by: null
implemented_at: null
related: "#87"
---

# 設計提案: lang/go Part を追加する

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

`template/parts/lang/`は`python`・`typescript`・`rust`のみで、Go環境を`--lang go`で
生成できません。CLIは`template/parts/lang/`を動的スキャンするため、`lang/go`ディレクトリを
追加するだけで`--lang go`が有効になります(コード変更不要)。

`lang/rust`(#86)と異なり、`lang/go`は#94(`base`の`__pycache__/`整理)がマージ済みの状態で
着手するため、最初から正しい前提(`base`はlang非依存、Pythonが混入しない)で設計できます。

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| `template/parts/lang/go/`(part.toml + payload/)の追加 | `starter/*`のGo版スケルトン(`starter/cli-go`等。#91が確立したパターンに従い、必要になった時点で別Issue) |
| 既存`lang/python`・`lang/typescript`・`lang/rust`の`conflicts`への`lang/go`追加 | 複数lang同時指定・flake.nixの`append`マージ戦略(U-06、フェーズ5) |

## 3. 選択肢

### 3.1. Goツールチェインの供給元

| 案 | 内容 | 評価 |
| --- | --- | --- |
| A | nixpkgs標準パッケージ`go`(コンパイラ・`gofmt`・`go vet`・`go test`を内包)+`golangci-lint`を直接使用 | ← 推奨。既存`lang/python`・`lang/typescript`・`lang/rust`と同じく、新規flake inputを追加せずnixpkgsチャンネルだけでバージョンを固定する既存パターンと一貫する |
| B | `gvm`等のバージョンマネージャ経由 | 見送り。Nixストア外への可変ダウンロードが発生し再現性が失われる |

### 3.2. プレースホルダーの配置

| 案 | 内容 | 評価 |
| --- | --- | --- |
| A | `go.mod`・`main.go`をリポジトリルートに配置 | ← 推奨。Goのエコシステム慣習(単一バイナリ構成では`src/`を介さずルート直下に置くのが一般的)に合わせる |
| B | `lang/rust`の`src/main.rs`に倣い`src/main.go`に配置 | 見送り。Rustの`src/main.rs`はCargoの規約に基づく配置であり、Goには同種の規約が無い。Go開発者にとって不自然な構成になる |

案Aを採用します。lang毎にプレースホルダーの配置がエコシステム慣習に従って異なる(rustは
`src/`配下、goはルート直下)ことは、starterとlangの責任分離(#91)がプレースホルダーの
物理配置まで統一することを要求しないため問題ありません。

## 4. 設計案

### 4.1. `part.toml`

```toml
[part]
id = "lang/go"
layer = "lang"
summary = "Go言語環境（go / gofmt / golangci-lint）"
requires = ["base"]
conflicts = ["lang/python", "lang/typescript", "lang/rust"]

[placeholders]
required = ["project_name"]

[[files]]
path = "flake.nix"
strategy = "replace"

[[files]]
path = "treefmt.nix"
strategy = "replace"

[[files]]
path = "justfile"
strategy = "replace"

[[files]]
path = "go.mod"
strategy = "replace"

[[files]]
path = "main.go"
strategy = "replace"

[[files]]
path = "main_test.go"
strategy = "replace"

[[files]]
path = ".gitignore"
strategy = "replace"
```

### 4.2. `flake.nix`（base差分）

`devShells.default.packages`に追加:

```nix
pkgs.go
pkgs.golangci-lint
```

`go`パッケージが`gofmt`・`go vet`・`go test`・`go build`を内包するため、rustの
`clippy`/`rustfmt`のような追加パッケージは不要です。`golangci-lint`はGoコミュニティの
標準的な集約リンター(`go vet`・`staticcheck`・`errcheck`等をラップ)で、`ruff`・`biome`・
`clippy`と同じ「主要lintツールを明示的にdevShellへ含める」既存パターンに合わせます。

### 4.3. `treefmt.nix`（base差分）

```nix
programs.gofmt.enable = true;
```

treefmt-nix標準のgofmtモジュールを使用します。

### 4.4. `justfile`（base差分）

```just
# requires: treefmt, golangci-lint
lint:
    treefmt --fail-on-change
    golangci-lint run ./...

# requires: go
test:
    go test ./...

verify: lint check-docs check-readme check-status check-encoding test
```

`just versions`に`go version`・`golangci-lint version`を追加します。

### 4.5. 最小プレースホルダーの必要性

`go build`・`go test`・`go vet`は`go.mod`(モジュールマニフェスト)が無いと
「go.mod file not found」で即エラー終了します。`starter/*`は#91でlang非依存の骨格のみに
なっており、Go版の骨格(`starter/cli-go`等)も無いため、`lang/go`単体で`just verify`を
グリーンに保つには`lang/go`自身が最小限の`go.mod`・`main.go`を提供する必要があります
(rustと同じ理由、`lang/rust`設計提案4.5節を参照)。

```text
# go.mod
module {{project_name}}

go 1.23
```

```go
// main.go — Generated placeholder — delete when you add real code
package main

import "fmt"

func main() {
	fmt.Println("Hello, {{project_name}}!")
}
```

```go
// main_test.go — Generated placeholder — delete when you add real code
package main

import "testing"

func TestPlaceholder(t *testing.T) {}
```

Goの慣習に従い、ユニットテストは同一パッケージ内の`_test.go`ファイルに分離します
(Rustの`#[cfg(test)] mod tests`とは配置形式が異なりますが、いずれも各言語のプレースホルダー
テストという役割は同じです)。`go 1.23`はNixpkgsチャンネル(`nixos-25.11`)が提供する
実際のGoバージョンに合わせて実装時に検証・調整します。

### 4.6. `.gitignore`

`base`全文 + Go向けの標準的なビルド成果物パターン(GitHub公式`Go.gitignore`テンプレートに
準拠)を追加します。

```text
# === Go ===
*.exe
*.exe~
*.dll
*.so
*.dylib
*.test
*.out
```

`lang/rust`の`target/`のような単一ディレクトリの慣習がGoには無いため(`go build`は既定で
カレントディレクトリにバイナリを出力する)、拡張子ベースの標準パターンを採用します。

### 4.7. 既存Partへの影響

`lang/python`・`lang/typescript`・`lang/rust`の`part.toml`の`conflicts`に`lang/go`を
追加します(ペア方式の双方向管理、#86と同じ対応)。

## 5. 失敗とロールバック

- 追加ファイルのみで既存生成物(python/typescript/rustプロファイル)への影響はありません
- `conflicts`追加は既存挙動を変えません(新しい組み合わせを禁止する側の変更のみ)
- `.py`/`.ts`と異なり`.go`ファイルを無条件requiresで同梱する既存Partは無いため、#94で
  発見した`inject`経由の混入経路と同種の問題は発生しません(`lang/go`自体が`.gitignore`を
  提供し、将来`features/logging-go`等を追加する場合は`requires=["lang/go"]`を必須とします)
- ロールバックは`git revert`で可能です

## 6. 検証

| テスト層 | 検証内容 |
| --- | --- |
| `tests/unit/test_schema.py` | `lang/go`のpart.tomlがスキーマ検証を通ること |
| `tests/e2e/test_generate_profiles.py` | `--lang go`で生成した`flake.nix`に`go`/`golangci-lint`が含まれること、`.gitignore`に`*.exe`等が含まれ`__pycache__/`は含まれないこと |
| 手動確認 | 生成プロジェクトで`nix develop --command go version`・`nix develop --command just verify`がグリーン |
| `just verify`（このリポジトリ） | 全チェックpass |

## 7. 未解決事項

- **GoのStarter Part**: `starter/*`のGo版役割別スケルトンは、必要になった時点で#91が
  確立したパターン(`starter/cli-go`等)に従って別Issueで追加します
- **`go.mod`のバージョン固定**: `go 1.23`は暫定値。実装時にNixpkgsチャンネルが提供する
  実際のGoバージョンを確認し調整します
- **バージョン固定の柔軟性**: 特定のGoマイナーバージョンへの厳密な固定が必要になった場合は、
  要件化された時点で改めて検討します(rust同様U-06関連でフェーズ5に先送り)
