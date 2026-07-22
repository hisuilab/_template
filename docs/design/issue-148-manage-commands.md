---
status: approved
proposed_at: 2026-07-23
approved_at: 2026-07-23
approved_by: PM
implemented_at: 2026-07-23
related: "#148"
---

# 設計提案: `/manage` コマンド群を Claude Code スラッシュコマンドとして登録する

状態はfrontmatter(`status`・`proposed_at`・`approved_at`・`approved_by`・`implemented_at`・
`related`)が正本です。

## 目次

- [1. 問題](#1-問題)
- [2. 対象範囲](#2-対象範囲)
- [3. 選択肢](#3-選択肢)
- [4. 設計案](#4-設計案)
  - [4.1. ファイル構成](#41-ファイル構成)
  - [4.2. 各ファイルの形式](#42-各ファイルの形式)
- [5. 失敗とロールバック](#5-失敗とロールバック)
- [6. 検証](#6-検証)
- [7. 未解決事項](#7-未解決事項)

## 1. 問題

PR #146 で `agent-workflow/commands/manage.md` が追加され、`/manage:status`・`/manage:assign`・
`/manage:cleanup` の3コマンドが仕様として定義されました。しかし `.claude/commands/manage/`
ディレクトリが存在しないため、Claude Code がこれらをスラッシュコマンドとして認識できず
`Unknown command` エラーが発生します。

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| `.claude/commands/manage/README.md`(新規) | `agent-workflow/commands/manage.md` の内容変更 |
| `.claude/commands/manage/status.md`(新規ラッパー) | `scripts/worktree-safety` の変更 |
| `.claude/commands/manage/assign.md`(新規ラッパー) | `features/ai-agent` テンプレートへの反映 |
| `.claude/commands/manage/cleanup.md`(新規ラッパー) |  |

## 3. 選択肢

| # | 内容 | 評価 |
| --- | --- | --- |
| A | `.claude/commands/manage/` に薄いラッパーファイルを作成し、`agent-workflow/commands/manage.md` の各節へ委譲する | 既存コマンドと同一パターン。実行契約の正本を `agent-workflow/` に保ちながら登録できる。採用案 |
| B | `agent-workflow/commands/manage.md` の内容を `.claude/commands/manage/` に直接複製する | 実行契約が二重管理になり同期コストが発生する。不採用 |

採用案はAです。

## 4. 設計案

### 4.1. ファイル構成

```text
.claude/
└── commands/
    └── manage/
        ├── README.md      (新規: ディレクトリ概要)
        ├── status.md      (新規ラッパー → manage.md 2節)
        ├── assign.md      (新規ラッパー → manage.md 3節)
        └── cleanup.md     (新規ラッパー → manage.md 4節)
```

### 4.2. 各ファイルの形式

既存コマンドラッパー（`status.md`・`think/investigate.md` 等）と同じ形式を使います。
ファイル先頭に管理責任・権限・承認などのメタ情報を記載し、
`agent-workflow/commands/manage.md` を読んで対応節の指示に従うよう参照します。

`status.md` の例:

```markdown
管理責任: primary manager worktreeから並列Issue worktreeの状態を観測します。
...

`../../../../agent-workflow/commands/manage.md`を読み、`2. manage:status`の指示に従ってください。
```

## 5. 失敗とロールバック

| ケース | 影響 | 対応 |
| --- | --- | --- |
| ラッパーファイルのパスが誤っている | コマンド起動時に `agent-workflow/commands/manage.md` を読み込めない | 相対パスを `git show` で確認し、修正する |
| `manage/` ディレクトリが認識されない | スラッシュコマンドとして補完されない | Claude Code を再起動して認識させる |

## 6. 検証

| 層 | 検証内容 |
| --- | --- |
| 文書 | frontmatter・です・ます調を確認する |
| リンク | ラッパーからの相対パスが `agent-workflow/commands/manage.md` を正しく指すことを確認する |
| 既存検証 | `just verify` がグリーンであることを確認する |
| 動作確認 | `/manage:status` を呼び出したときに `manage.md` の内容がロードされることを会話内で確認する |

## 7. 未解決事項

| ID | 論点 | 決定者 | ブロックする作業 |
| --- | --- | --- | --- |
| U-01 | `features/ai-agent` テンプレートへ `manage/` ラッパーを反映するか | Issue #116 相当 | 生成プロジェクトへの伝播 |
