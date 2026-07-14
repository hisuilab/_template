---
status: implemented
proposed_at: 2026-07-14
approved_at: 2026-07-14
approved_by: PM
implemented_at: 2026-07-14
related: "#60"
---

# 設計提案: purpose/* Parts を starter/* に改名する

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

`docs/architecture/core.md` §6.3 で確定した設計方針では、用途別スターター Part のレイヤーを
`purpose` から `starter` に改名します。現行の `purpose/*` という名称は「用途で分ける」という
分類軸を示しますが、将来追加する `architecture/*` との関係（「アーキテクチャを持たない即動く
スターター」）が名前から読み取れません。`starter` に改名することで役割の意図が明確になります。

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| `template/parts/purpose/` ディレクトリ改名 | `scale/*`・`architecture/*` の実装 |
| `part.toml` の `id`・`layer` フィールド更新 | `inject` サブコマンド（Issue #59） |
| `template/schema/part_schema.py` の `LAYERS` 定数更新 | `scale/medium`・`scale/large` 実装 |
| `template/profiles/small-*.toml` → `starter-*.toml` ファイル改名と内容更新 | ユーザー向けエイリアス・移行ガイド |
| テスト一式の更新（unit / e2e / fixtures） |  |
| `docs/architecture/core.md` §2 現行実装テーブルの更新 |  |

## 3. 選択肢

代替案なし。`docs/architecture/core.md` §6.3 で確定済みの変更であり、実装方針は一意。

## 4. 設計案

### 4.1. 変更ファイル一覧

| ファイル / ディレクトリ | 変更内容 |
| --- | --- |
| `template/parts/purpose/` | `template/parts/starter/` にリネーム |
| `template/parts/starter/cli/part.toml` | `id = "starter/cli"`、`layer = "starter"` |
| `template/parts/starter/web-api/part.toml` | `id = "starter/web-api"`、`layer = "starter"` |
| `template/parts/starter/library/part.toml` | `id = "starter/library"`、`layer = "starter"` |
| `template/schema/part_schema.py` | `LAYERS` の `"purpose"` → `"starter"` |
| `template/profiles/small-cli.toml` → `starter-cli.toml` | ファイルリネーム＋`"purpose/cli"` → `"starter/cli"` |
| `template/profiles/small-web-api.toml` → `starter-web-api.toml` | ファイルリネーム＋`"purpose/web-api"` → `"starter/web-api"` |
| `template/profiles/small-library.toml` → `starter-library.toml` | ファイルリネーム＋`"purpose/library"` → `"starter/library"` |
| `tests/unit/test_generator.py` | `purpose/*` → `starter/*`、`layer="purpose"` → `layer="starter"` |
| `tests/unit/test_schema.py` | `purpose/cli` → `starter/cli` |
| `tests/fixtures/schema/valid_profile.toml` | `purpose/cli` → `starter/cli` |
| `tests/e2e/test_generate_profiles.py` | `small-cli` → `starter-cli`、`small-web-api` → `starter-web-api`、`small-library` → `starter-library` |
| `docs/architecture/core.md` §2 | `purpose` → `starter`（現行実装テーブル） |

### 4.2. 実装順序

依存が浅い層から変更します。

1. `template/schema/part_schema.py` — `LAYERS` 定数更新（`"purpose"` → `"starter"`）
2. `template/parts/` — ディレクトリリネームと `part.toml` 更新
3. `template/profiles/` — ファイルリネームと Part 参照更新
4. テスト一式の更新
5. `docs/architecture/core.md` §2 更新

## 5. 失敗とロールバック

- 本変更は純粋なリネームであり、ビヘイビアの変更を含まない
- `just verify`（unit / e2e / schema validation）が全パスすることで正しさを確認できる
- ロールバックは `git revert` で可能

## 6. 検証

| テスト層 | 検証内容 |
| --- | --- |
| `tests/unit/test_schema.py` | `LAYERS` に `"starter"` が含まれ `"purpose"` が拒否されること |
| `tests/unit/test_generator.py` | `starter/cli` Part が読み込めること |
| `tests/e2e/test_generate_profiles.py` | `starter-cli` / `starter-web-api` / `starter-library` プロファイルで生成が成功すること |
| `just verify` | `check-readme`・`check-status`・rumdl・treefmt がすべてパスすること |

## 7. 未解決事項

なし。本変更はすべて確定済みの設計方針（`docs/architecture/core.md` §6.3）の実装です。
