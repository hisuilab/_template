---
status: proposed
proposed_at: 2026-07-20
approved_at: null
approved_by: null
implemented_at: null
related: "#100"
---

# 設計提案: lang/rustのCargo.tomlに基盤依存を組み込む

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

「Nix開発テンプレート改善方針」(ベース/用途別の分離)の提案は、Rustの「必須」として
`tracing`・`tracing-subscriber`・`serde`・`serde_json`・`anyhow`・`thiserror`を挙げて
います。現状`lang/rust`が提供する`Cargo.toml`は依存ゼロのプレースホルダーで、これらは
一切含まれていません。

`lang/rust`は既に`Cargo.toml`を持っている(#86で追加済み。cargoがマニフェスト無しでは
動作しないため)ため、4言語の中で最も着手しやすい対象です。

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| `lang/rust`の`Cargo.toml`への基盤依存追加、`main.rs`プレースホルダーの更新 | `starter/web-api-rust`等の用途別複合Part追加(#98の後続Issue) |
| 生成プロジェクトでの`cargo build`/`test`/`clippy`の手動確認 | Python/TypeScript/Goの同種対応(それぞれ別Issue) |

## 3. 選択肢

| 案 | 内容 | 評価 |
| --- | --- | --- |
| A | `lang/rust`のCargo.toml自体に基盤依存を直接組み込む | ← 推奨。既存の「`lang/*`＝その言語のbase」という設計と一致する。`features/logging-python`と異なり「ほぼ全員が使う土台」という提案の趣旨に対してopt-in運用は不自然 |
| B | `features/foundation-rust`という新規opt-in Partとして分離する | 見送り。opt-in運用は「ほぼ全員が使う」という前提と矛盾する。加えて将来`starter/web-api-rust`等がCargo.tomlをさらに拡張する際、baseとopt-in Partの2つを毎回合成する必要が生じ、#97で解消したばかりの複雑さが再発する |

案Aを採用します。

## 4. 設計案

### 4.1. `Cargo.toml`への依存追加

```toml
[package]
name = "{{project_name}}"
version = "0.1.0"
edition = "2021"

[dependencies]
anyhow = "1"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
thiserror = "1"
tracing = "0.1"
tracing-subscriber = "0.3"
```

バージョンはメジャー(または明確に安定している行)のみ指定し、パッチバージョンはcargoの
解決に委ねます(既存のNixパッケージバージョン指定方針と同様、厳密な固定はしません)。

### 4.2. `main.rs`の更新

`tracing`・`anyhow`は実際にコード内で使用する形にし、依存が「宣言だけで未使用」に
ならないようにします。`serde`・`serde_json`・`thiserror`は具体的な構造体やエラー型を
プレースホルダーへ持ち込むと恣意的な例になるため、依存としては利用可能にしつつ
コード上は使用を強制しません(cargoは未使用依存を警告しないため実害はありません)。

```rust
// Generated placeholder — delete when you add real code
use anyhow::Result;

fn main() -> Result<()> {
    tracing_subscriber::fmt::init();
    tracing::info!("Hello, {{project_name}}!");
    Ok(())
}

#[cfg(test)]
mod tests {
    #[test]
    fn placeholder() {}
}
```

### 4.3. 将来の用途別複合Partとの関係

`starter/web-api-rust`(#98の後続Issue)は`requires=["lang/rust", ...]`かつ`Cargo.toml`を
`strategy="replace"`で提供する想定です。既存のresolver(依存Partを先に適用)+planner
(後発の`replace`が勝つ)の仕組みにより、`starter/web-api-rust`のCargo.tomlは
「本Issueで確立したbase依存 + axum/tokio/reqwest」という**累積的なスーパーセット**として
書くことになります。新しい合成機構は不要ですが、後続Issueの実装時に本Issueの依存一覧を
書き写す(重複させる)必要がある点は、`flake.nix`/`treefmt.nix`と同様のトレードオフとして
残ります(#97の未解決事項と同種)。

## 5. 失敗とロールバック

- 追加ファイルの変更のみで、他Part(`starter/*-python`等)への影響はありません
- `cargo build`は初回、crates.ioへのネットワークアクセスが必要です(Nixサンドボックス外の
  cargoの標準動作。既存の`lang/rust`も同じ前提)。オフライン環境での初回ビルド失敗は
  想定内の制約としてREADMEに明記します
- ロールバックは`git revert`で可能です

## 6. 検証

| テスト層 | 検証内容 |
| --- | --- |
| `tests/e2e/test_generate_profiles.py` | 生成した`Cargo.toml`に`tracing`・`serde`・`anyhow`等が含まれること |
| 手動確認 | 生成プロジェクトで`nix develop --command cargo build`・`cargo test`・`cargo clippy`が成功すること |
| `just verify`(このリポジトリ) | 全チェックpass |

## 7. 未解決事項

- **依存の重複**: 4.3節の通り、将来`starter/web-api-rust`等がCargo.tomlを拡張する際、
  本Issueのbase依存一覧を手動で書き写す必要があります。Nix側のimport機構(#97)のような
  仕組みはCargo.toml(TOML、構造化データ)には直接使えないため、都度PMの判断で許容します
- **Python/TypeScript/Goへの横展開**: 本Issueが確立したパターン(lang自体へ基盤依存を
  組み込む)を、マニフェストが無いPython/TypeScript(pyproject.toml/package.jsonの新設が
  前提)・Go(go.sum生成の検証が必要)へ適用するのは別Issueとします
