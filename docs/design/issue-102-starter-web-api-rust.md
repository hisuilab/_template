---
status: proposed
proposed_at: 2026-07-20
approved_at: null
approved_by: null
implemented_at: null
related: "#102"
---

# 設計提案: starter/web-api-rust複合Partを追加する

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

「Nix開発テンプレート改善方針」のRust Web API用途(axum/tokio/reqwest)を、#91で確立した
`starter/<purpose>-<lang>`複合Partパターン(現状`-python`のみ)で実現します。#100で
`lang/rust`のCargo.tomlに基盤依存(tracing/serde/anyhow/thiserror等)を組み込んだので、
本Issueはその上にWeb API向け依存を積みます。

本Issueは#88(Axum+HTMX+Pico方針)の土台にもなります。axum実装が整えば、#88はその上に
Askama(テンプレートエンジン)+HTMX+Pico CSSを追加するだけで着手できます。

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| `template/parts/starter/web-api-rust/`(part.toml + payload/)の追加 | Askama/HTMX/Pico CSSの追加(#88で対応) |
| `Cargo.toml`(#100の基盤依存+axum/tokio/reqwest)・`src/main.rs`(axumサーバー) | ルーティング構成の作り込み(用途別Partのプレースホルダーとしては最小限に留める) |

## 3. 選択肢

| 案 | 内容 | 評価 |
| --- | --- | --- |
| A | `Cargo.toml`+`src/main.rs`(axum健康チェックエンドポイント程度の最小サーバー)を提供 | ← 推奨。`starter/web-api-python`のFastAPI版(`src/app.py`)と同等の最小実装。#91の複合Partパターンをそのまま踏襲 |
| B | ルーティング・DB接続等を含む本格的な構成にする | 見送り。用途別Partのプレースホルダーとしては過剰で、starterの「即動くスターター」という性質(`docs/architecture/core.md`)から外れる |

案Aを採用します。

## 4. 設計案

### 4.1. `part.toml`

```toml
[part]
id = "starter/web-api-rust"
layer = "starter"
summary = "starter/web-api の Rust 実装（axum + tokio + reqwest）"
requires = ["base", "starter/web-api", "lang/rust"]
conflicts = []

[placeholders]
required = ["project_name"]

[[files]]
path = "Cargo.toml"
strategy = "replace"

[[files]]
path = "src/main.rs"
strategy = "replace"
```

`lang/rust`も`Cargo.toml`・`src/main.rs`を`strategy="replace"`で提供しますが、resolverが
`requires`(`lang/rust`が`starter/web-api-rust`の依存)に基づき`lang/rust`を先に適用するため、
plannerの「後発の`replace`が勝つ」規則により`starter/web-api-rust`側の内容が最終的に採用
されます(#100設計書4.3節で確認済みの仕組み、新しい合成機構は不要)。

### 4.2. `Cargo.toml`(累積的なスーパーセット)

`lang/rust`の基盤依存(#100)を含んだ上でaxum関連を追加します。

```toml
[package]
name = "{{project_name}}"
version = "0.1.0"
edition = "2021"

[dependencies]
anyhow = "1"
axum = "0.8"
reqwest = { version = "0.12", features = ["json"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
thiserror = "1"
tokio = { version = "1", features = ["full"] }
tracing = "0.1"
tracing-subscriber = "0.3"
```

依存の重複(基盤依存をここでも列挙する必要がある点)は#100設計書7節で既に受容済みの
トレードオフです。

### 4.3. `src/main.rs`(axum最小サーバー)

```rust
// Generated placeholder — delete when you add real code
use anyhow::Result;
use axum::{routing::get, Router};

async fn health() -> &'static str {
    "ok"
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt::init();

    let app = Router::new().route("/health", get(health));

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await?;
    tracing::info!("listening on {}", listener.local_addr()?);
    axum::serve(listener, app).await?;
    Ok(())
}

#[cfg(test)]
mod tests {
    #[test]
    fn placeholder() {}
}
```

`reqwest`はWeb API用途で外部サービス呼び出しに使う想定の依存であり、この最小プレースホルダー
では未使用のまま宣言します(#100で確認済みの通り、cargoは未使用依存を警告しません)。

### 4.4. `starter/web-api`骨格との共存

`starter/web-api`(骨格Part)が提供する`src/README.md`・`src/routes/README.md`は、
`starter/web-api-rust`の`src/main.rs`と別ファイルのため衝突なく共存します(#91で確認済みの
パターン)。

## 5. 失敗とロールバック

- 追加Partのみで、`starter/cli`・`starter/library`等の既存プロファイルへの影響はありません
- `--lang rust`+`starter-cli`のような組み合わせでは`starter/web-api-rust`は注入されず
  (`_starter_lang_parts`が`starter/web-api-rust`のような対応するIDが無ければ何も注入しない
  #91の仕組みのまま)、`lang/rust`単体のプレースホルダーが引き続き使われます(回帰なし)
- ロールバックは`git revert`で可能です

## 6. 検証

| テスト層 | 検証内容 |
| --- | --- |
| `tests/e2e/test_generate_profiles.py` | `--lang rust`+`starter-web-api`で生成した`Cargo.toml`にaxum等が含まれること、`src/main.rs`が存在すること |
| 手動確認 | 生成プロジェクトで`cargo build`/`cargo test`/`cargo clippy`が成功すること。実際にサーバーを起動し`/health`エンドポイントへのリクエストが成功すること |
| `just verify`(このリポジトリ) | 全チェックpass |

## 7. 未解決事項

- **#88(HTMX)**: 本Issue完了後、Askama+HTMX+Pico CSSをこの上に追加する形で着手します
- **`starter/cli-rust`・`starter/library-rust`**: 本Issueと同型のパターンで、必要になった
  時点で別Issueとして追加します
