# 文書更新ポリシー

変更時にどの文書を更新すべきかを定義します。更新漏れなく最小限の文書だけを触れるようにするための正本です。

## 目次

- [1. 基本方針](#1-基本方針)
- [2. 正本マップ](#2-正本マップ)
- [3. 変更トリガー別更新先](#3-変更トリガー別更新先)
- [4. 更新しない判断](#4-更新しない判断)

## 1. 基本方針

- 文書は「変更理由が同じもの」だけを更新します。ついで修正は別コミット / PR にします
- 同じ情報を複数箇所で正本化しません。リンクで参照します
- 非自明な判断は `docs/decisions/` へ記録します
- `docs/draft/` はプロトタイプ完了後に廃止します。確定した情報は適切な正本ディレクトリへ移行します

## 2. 正本マップ

| 問い | 正本 | 更新タイミング |
| --- | --- | --- |
| 何を作るか | [`docs/requirements/`](../requirements/) | 利用者・価値・対象範囲・フェーズが変わる時 |
| どう作るか | [`docs/architecture/`](../architecture/) | 責務境界・依存方向・Part 構成が変わる時 |
| なぜその方式を選んだか | [`docs/decisions/`](../decisions/) | 非自明な判断をした時 |
| Issue 単位の設計詳細 | [`docs/design/`](../design/) | Issue を設計する時・実装で変わる時 |
| どの順序で作るか | [`docs/milestones/`](../milestones/) | 対象範囲・依存順・完了条件が変わる時 |
| 開発・運用手順 | [`docs/development/`](.) | 開発手順・検証手順・文書ポリシーが変わる時 |
| AI エージェントの動作 | `.claude/rules/` | 権限・Role・Workflow・Command が変わる時 |

## 3. 変更トリガー別更新先

| 変更内容 | 更新する文書 |
| --- | --- |
| 利用者・提供価値・対象範囲の変更 | `docs/requirements/product.md` |
| Part 構成・レイヤー設計の変更 | `docs/architecture/core.md` |
| モジュール責務・依存方向の変更 | `docs/architecture/core.md` |
| 新しい設計判断（非自明なもの） | `docs/decisions/YYYY-MM-DD-slug.md` |
| Issue の設計・実装方針 | `docs/design/issue-N-slug.md` |
| マイルストーンの完了条件・計画 | `docs/milestones/m{N}-slug.md` |
| 文書ポリシー・状態管理ルール | `docs/development/documentation-policy.md` / `docs/development/document-status.md` |
| AI ワークフロー・権限・Role | `.claude/rules/` 配下の該当ファイル |

## 4. 更新しない判断

以下の場合は文書を更新しません。

- コードの実装詳細（コードが正本）
- テストの個別ケース（`tests/` 配下が正本）
- フォーマット・lint の修正のみの変更
- 推測や仮説（確定したものだけを文書化します）
