# docs/milestones

## 1. 概要

マイルストーン単位の詳細設計・完了条件を管理するディレクトリです。

## 2. 責任

- 保持するもの: マイルストーン文書（`m{N}-slug.md`）

## 3. 責任外

- 要件・アーキテクチャの上位方針（`docs/draft/project-direction.md` が持ちます）

## 4. 凡例

| status | 意味 |
| --- | --- |
| `not_started` | 未着手 |
| `in_progress` | 進行中 |
| `done` | 完了 |

## 5. マイルストーン一覧

| # | 文書 | タイトル | フェーズ | 状態 |
| --- | --- | --- | --- | --- |
| M1 | [m1-tree-structure.md](m1-tree-structure.md) | template/ レイヤー設計とプロファイル骨格 | フェーズ2 | done |
| M2 | [m2-payload-impl.md](m2-payload-impl.md) | template/parts/ payload 実装 | フェーズ2 | done |
| M3 | [m3-generator-impl.md](m3-generator-impl.md) | tooling/generator/ パイプライン実装 | フェーズ2 | done |
| M4 | [m4-e2e-integration.md](m4-e2e-integration.md) | エンドツーエンド統合と prototype → main PR | フェーズ2 | done |
| M5 | [m5-lang-part.md](m5-lang-part.md) | lang/ Part 追加と --lang フラグ実装 | フェーズ2 | done |
| M6 | [Issue #2](https://github.com/hisuilab/_template/issues/2) | TypeScript lint 整備（Biome 導入） | フェーズ3 | done |
| M7 | [Issue #3](https://github.com/hisuilab/_template/issues/3) | nix run flake app 対応 | フェーズ3 | done |
| M8 | [Issue #7](https://github.com/hisuilab/_template/issues/7) | features/logging Part 追加（Python / TypeScript） | フェーズ3 | done |
| M9 | [Issue #12](https://github.com/hisuilab/_template/issues/12) | features/ai-agent Part 拡張（.claude scaffold） | フェーズ4 | done |
| M10 | [Issue #13](https://github.com/hisuilab/_template/issues/13) | init-workspace サブコマンド追加 | フェーズ4 | done |
| M11 | [Issue #40](https://github.com/hisuilab/_template/issues/40) | features/github-rulesets Part 追加 | フェーズ4 | in_progress |
