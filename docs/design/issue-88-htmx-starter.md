---
status: proposed
proposed_at: 2026-07-21
approved_at: null
approved_by: null
implemented_at: null
related: "#88"
---

# 設計提案: html/css/js/htmx 向け starter Part を追加する

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

Rust Web開発方針(プロトタイピング段階: Axum + HTMX + Pico CSS + Askama、本格実装段階では
React/Next.jsへ移行可能)を実現する用途別Partを追加します。#91で確立した
`starter/<purpose>-<lang>`複合Partパターンにより、starterがlang別に中身を出し分けられない
という当初の制約は解消済みです。#102で`starter/web-api-rust`(axum、JSON API)が実装され、
axumのdevShell・基盤依存(#100)は既に整っています。

`starter/web-api-rust`は現状JSON APIを前提にしており、Askamaテンプレート・HTMX向け
HTMLレンダリング・静的アセット配信を持ちません。これをどう追加するかが本Issueの主題です。

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| 新規purpose「`web-htmx`」の追加(`template/profiles/starter-web-htmx.toml`・`starter/web-htmx`骨格・`starter/web-htmx-rust`複合Part) | 他言語(`web-htmx-python`等)の実装(必要になった時点で別Issue) |
| Askama + HTMX + Pico CSSによる最小サーバーレンダリングページ1枚の提供 | React/Next.jsへの移行手順そのものの実装(移行先が無いため対象外。設計上の考慮のみ) |
| 静的アセット(htmx.js・pico.css)の入手方針の決定 | `architecture/layered`・`architecture/ddd`との統合(将来の拡張として未解決事項に記載) |

## 3. 選択肢

### 3.1. `web-api`へ追加 vs 新規purpose

| 案 | 内容 | 評価 |
| --- | --- | --- |
| A | 新規purpose「`web-htmx`」として`starter/web-api`とは独立に追加(新規profile・新規骨格Part・新規複合Part) | ← 推奨。JSON API(`starter-web-api`)とサーバーレンダリングHTMX(`starter-web-htmx`)は出発点として別物であり、既存の`starter/cli`・`starter/web-api`・`starter/library`という「purpose = 選択可能な出発点」という設計と一貫する。`Cargo.toml`/`main.rs`の所有権競合も発生しない(別Part・別ファイルパス) |
| B | `features/htmx-rust`として既存`starter/web-api-rust`に追加注入する | 見送り。`main.rs`の所有権が競合する(#100・#102と同じ`strategy=replace`の仕組みは使えるが、features Partがaxumのセットアップごと丸ごと書き直す必要があり「featuresは既存ファイルへの後付け」という既存の役割から逸脱する) |

案Aを採用します。

### 3.2. 静的アセット(htmx.js・pico.css)の入手方針

| 案 | 内容 | 評価 |
| --- | --- | --- |
| A | CDN経由(`<script src="https://unpkg.com/htmx.org@...">`等) | ← 本Issueで採用。実装が単純で、htmx公式のクイックスタートと同じ形。オフライン再現性は失うが、プロトタイピング段階(方針書の「検証速度を重視」)の趣旨と合致する |
| B | Nixで固定バージョンを取得しpayloadへvendoringする | 見送り(本Issueの対象外、7節の未解決事項)。`flake.nix`の`fetchurl`等でハッシュ固定は可能だが、実装にはネットワークアクセスでの実ファイル取得・ハッシュ確認が必要で、本セッションでは実施できない |

案Aを採用し、オフライン再現性の欠如は明示的な未解決事項として記録します。

## 4. 設計案

### 4.1. 新規profile: `template/profiles/starter-web-htmx.toml`

```toml
[profile]
name = "starter-web-htmx"
summary = "スターター HTMX(サーバーレンダリング)サービス向けプロファイル"
parts = [
  "base",
  "scale/small",
  "starter/web-htmx",
  "features/ai-agent",
  "features/github-rulesets",
  "features/github-project",
]

[variables]
```

`starter-web-api.toml`と同型です。

### 4.2. 骨格Part: `template/parts/starter/web-htmx/`

```toml
[part]
id = "starter/web-htmx"
layer = "starter"
summary = "HTMX(サーバーレンダリング)サービス向けの src 骨格（lang非依存）"
requires = ["base"]
conflicts = []

[placeholders]
required = ["project_name"]
```

`payload/templates/README.md`・`payload/static/README.md`(lang非依存の骨格、check-readme対応)
を提供します。

### 4.3. 複合Part: `template/parts/starter/web-htmx-rust/`

```toml
[part]
id = "starter/web-htmx-rust"
layer = "starter"
summary = "starter/web-htmx の Rust 実装（axum + askama + HTMX + Pico CSS）"
requires = ["base", "starter/web-htmx", "lang/rust"]
conflicts = []

[placeholders]
required = ["project_name"]

[[files]]
path = "Cargo.toml"
strategy = "replace"

[[files]]
path = "src/main.rs"
strategy = "replace"

[[files]]
path = "templates/layout.html"
strategy = "replace"

[[files]]
path = "templates/index.html"
strategy = "replace"

[[files]]
path = "templates/message.html"
strategy = "replace"
```

`Cargo.toml`は#100・#102と同じ累積的なスーパーセット方針で、`lang/rust`の基盤依存 +
`askama`・`askama_axum`・`tower-http`(静的ファイル配信用)を追加します。

```toml
[dependencies]
anyhow = "1"
askama = "0.12"
askama_axum = "0.4"
axum = "0.8"
reqwest = { version = "0.12", features = ["json"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
thiserror = "1"
tokio = { version = "1", features = ["full"] }
tower-http = { version = "0.6", features = ["fs"] }
tracing = "0.1"
tracing-subscriber = "0.3"
```

`src/main.rs`はaxumで`/`(全体ページ)・`/message`(HTMXの`hx-get`が差し替える部分フラグメント)
をAskamaテンプレートでレンダリングし、`/static`を`tower-http`の`ServeDir`で配信する最小構成に
します。`askama_axum`(0.4系)は`Template`への自動`IntoResponse`実装を提供しないため、
`askama_axum::into_response(&template)`で明示的に変換する必要があります(実装時に
`cargo build`で判明、設計時点の想定から修正)。

```rust
// Generated placeholder — delete when you add real code
use anyhow::Result;
use askama::Template;
use askama_axum::Response;
use axum::{Router, routing::get};
use tower_http::services::ServeDir;

#[derive(Template)]
#[template(path = "index.html")]
struct IndexTemplate {
    message: String,
}

#[derive(Template)]
#[template(path = "message.html")]
struct MessageTemplate {
    message: String,
}

async fn index() -> Response {
    askama_axum::into_response(&IndexTemplate {
        message: "Hello from HTMX!".to_string(),
    })
}

async fn message() -> Response {
    askama_axum::into_response(&MessageTemplate {
        message: "Reloaded via HTMX!".to_string(),
    })
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt::init();

    let app = Router::new()
        .route("/", get(index))
        .route("/message", get(message))
        .nest_service("/static", ServeDir::new("static"));

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

`hx-get="/message" hx-target="#message" hx-swap="outerHTML"`のボタンは`/`ではなく専用の
`/message`エンドポイントを叩きます。`/`が返す全体ページをそのまま`#message`へ差し込むと
HTMLがネストして壊れるため、部分フラグメント専用のルートを分けています。

`templates/index.html`(Askama、`{{ message }}`はAskamaのランタイム変数としてスペース付きで
記述。ジェネレータの`{{project_name}}`(スペース無し)とは記法上区別され、
`justfile`の`{{ part }}`と同じ回避パターンです。詳細は
[`docs/decisions/2026-07-13-justfile-parameter-vs-placeholder-escape.md`](../decisions/2026-07-13-justfile-parameter-vs-placeholder-escape.md)
参照):

```html
{% extends "layout.html" %}
{% block content %}
<h1>{{project_name}}</h1>
<p id="message">{{ message }}</p>
<button hx-get="/message" hx-target="#message" hx-swap="outerHTML">Reload</button>
{% endblock %}
```

`{{project_name}}`(スペース無し)はジェネレータが生成時に静的置換する部分(ページタイトル相当)、
`{{ message }}`(スペース付き)はAskamaが実行時に埋め込むテンプレート変数です。`templates/message.html`
は`/message`が返す部分フラグメント専用のテンプレートで、`<p id="message">{{ message }}</p>`のみを
含みます(4.3節参照)。

`templates/layout.html`はHTMXとPico CSSをCDN経由で読み込む共通レイアウトです。

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>{{project_name}}</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
  <script src="https://unpkg.com/htmx.org@2"></script>
</head>
<body>
  <main class="container">
    {% block content %}{% endblock %}
  </main>
</body>
</html>
```

HTMX・Pico CSSは3.2節の通りCDN経由のため、`static/`ディレクトリには`starter/web-htmx`骨格が
提供するREADME.md以外のファイルを本Issueでは追加しません(vendoringは7節の未解決事項)。

## 5. 失敗とロールバック

- 新規purpose・新規Partの追加のみで、既存`starter-cli`・`starter-web-api`・
  `starter-library`プロファイルへの影響はありません
- `lang/rust`単体(本複合Part無し)の生成結果は変更されません
- ロールバックは`git revert`で可能です

## 6. 検証

| テスト層 | 検証内容 |
| --- | --- |
| `tests/e2e/test_generate_profiles.py` | `--profile starter-web-htmx --lang rust`で生成した`Cargo.toml`にaskama等が含まれること、`templates/`・`src/main.rs`が存在すること |
| 手動確認 | 生成プロジェクトで`cargo build`/`test`/`clippy`が成功すること。サーバーを起動し`/`へのリクエストでHTMLが返り、HTMX属性(`hx-get`等)が含まれることを確認 |
| `just verify`(このリポジトリ) | 全チェックpass |

## 7. 未解決事項

- **静的アセットのオフライン再現性**: CDN経由(3.2節案A)は、この開発テンプレートの
  「Nixで再現可能な開発環境」という原則と厳密には整合しません。将来`fetchurl`等で
  vendoringする場合は別Issueとします
- **他言語への展開**: `web-htmx-python`(FastAPI+Jinja2+HTMX)等は、必要になった時点で
  本Issueと同型のパターンで別Issueとして追加します
- **architecture/layered・ddd との統合**: Rust Web開発方針が挙げるDomain/Service/Repository
  分離は、既存`architecture/layered`・`architecture/ddd` Partの責務と重なります。
  `starter/web-htmx-rust`を`architecture/*`と組み合わせる場合の設計は、実際にその規模の
  プロジェクトが必要になった時点で改めて検討します(本Issueは「即動くスターター」の
  最小構成に留めます)
- **React/Next.jsへの移行**: 移行先(`starter/web-htmx-typescript`や`architecture`込みの
  分離構成)は本Issueの対象外です
