---
status: proposed
proposed_at: 2026-07-22
approved_at: null
approved_by: null
implemented_at: null
related: "#138"
---

# 設計提案: `/think:investigate` を追加して Issue 着手前の事実確認フェーズを設ける

状態はfrontmatter(`status`・`proposed_at`・`approved_at`・`approved_by`・`implemented_at`・
`related`)が正本です。

## 目次

- [1. 問題](#1-問題)
- [2. 対象範囲](#2-対象範囲)
- [3. 選択肢](#3-選択肢)
- [4. 設計案](#4-設計案)
  - [4.1. コマンド仕様](#41-コマンド仕様)
  - [4.2. ファイル構成](#42-ファイル構成)
  - [4.3. ワイヤリング](#43-ワイヤリング)
  - [4.4. 既存コマンドとの区別](#44-既存コマンドとの区別)
- [5. 失敗とロールバック](#5-失敗とロールバック)
- [6. 検証](#6-検証)
- [7. 未解決事項](#7-未解決事項)

## 1. 問題

`/review:audit` などで指摘を受けて GitHub Issue 化した後、`/plan:issue` → `/auto:issue` で
着手する際に、mainブランチの実態・関連ブランチ・コードの現状を確認するフェーズが存在しない。

現状の `/plan:issue` は `gh issue view N` でIssue本文を読むだけで、次の検証を行わない。

- audit 指摘が既に main で修正済みかどうか
- 関連ブランチで並行作業中かどうか
- 指摘箇所のコードが Issue 本文の記述と一致しているかどうか

この状態で設計フェーズ(`/plan:design`)へ進むと、既に解消済みの問題の設計や、並行ブランチとの
競合を招く可能性がある。

既存の `/think:clarify`(仕様の曖昧さ解消)と `/think:risks`(変更リスク分類)は「これから何をするか」
を整理するフェーズであり、「Issue に書かれた事実が今のリポジトリで本当にそうか」を検証しない。

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| `agent-workflow/commands/think/investigate.md`(新規) | テストコードの変更 |
| `agent-workflow/commands/think/README.md`(更新) | `features/ai-agent` テンプレートへの反映 |
| `agent-workflow/rules/workflows.md`(更新) | Codex アダプター(`.codex/`)の変更 |
| `agent-workflow/commands/plan/issue.md`(更新) | `auto:milestone` への組み込み |
| `agent-workflow/commands/auto/issue.md`(更新) |  |
| `.claude/commands/think/investigate.md`(新規ラッパー) |  |
| `.claude/commands/think/README.md`(更新) |  |

## 3. 選択肢

| # | 内容 | 評価 |
| --- | --- | --- |
| A | `/think:investigate` を独立コマンドとして新設し、`/plan:issue` と `/auto:issue` の両方へ組み込む | フェーズが独立するため再利用可能。`/plan:issue` 単体でも事実確認を実施できる。採用案 |
| B | `/plan:issue` の手順を拡張して事実確認ステップを追加するのみ(独立コマンドなし) | `/auto:issue` への組み込みが `/plan:issue` 依存になり、独立呼び出しができなくなる。不採用 |
| C | `/think:clarify` を拡張して事実確認を含める | `clarify` の責任が「仕様曖昧さ解消 + 事実確認」に広がり、責任一意性が崩れる。不採用 |

採用案はAです。

## 4. 設計案

### 4.1. コマンド仕様

```text
コマンド名 : /think:investigate N  (N = Issue番号)
管理責任   : Issue 記載の事実をコード・ブランチで検証する。作成・更新はしない
ワークフロー: think (事前確認)
権限       : read-only
副作用     : 画面出力のみ
承認       : Critical な食い違いがある場合のみ、意思決定レポートで PM へ確認
```

**手順**:

1. `gh issue view N` で Issue 本文・ラベル・担当者を読む
2. `git log main --oneline -20` と指摘ファイルの `git blame` で「指摘が今の main にまだ
   あるか」を確認する
3. `git branch --all` で Issue番号・関連キーワードを含むブランチを一覧し、並行作業中の
   ブランチがないかを確認する
4. Issue 本文で言及されているファイル・シンボルをコードで確認する(存在確認・内容照合)
5. 調査レポートを出力する

**調査レポート形式**:

```text
## 調査レポート — issue-{N}

### 確認済み
- (Issue 本文の記述がコードと一致している点)

### 未確認
- (コードを読んでも確認できなかった点)

### 反証済み
- (Issue 本文の記述がコードと一致しない点。既修正・削除済み等)

### 関連ブランチ
- (並行作業中のブランチ一覧、なければ「なし」)

### 推奨
- plan へ進む / PM 確認が必要 / Issue クローズを検討
```

Critical な反証(指摘箇所が既に修正済み、Issue が重複等)がある場合は、`/plan:design` へ
進む前に意思決定レポートでPMへ確認する。

### 4.2. ファイル構成

```text
agent-workflow/
└── commands/
    └── think/
        ├── README.md          (更新: investigate を追記)
        ├── clarify.md         (変更なし)
        ├── risks.md           (変更なし)
        └── investigate.md     (新規)

.claude/
└── commands/
    └── think/
        ├── README.md          (更新: investigate を追記)
        ├── clarify.md         (変更なし)
        ├── risks.md           (変更なし)
        └── investigate.md     (新規ラッパー)

agent-workflow/rules/
└── workflows.md               (更新: フェーズ表・自然言語ルーティング)

agent-workflow/commands/
├── plan/issue.md              (更新: investigate ステップを手順に追加)
└── auto/issue.md              (更新: investigate フェーズを追加)
```

### 4.3. ワイヤリング

**`/plan:issue` への組み込み**:

手順2(`gh issue view N` で内容を確認)の直後に「事実確認ステップ」として
`think:investigate` の手順を実行する。結果に Critical な反証がある場合はブランチ作成前に
PMへ確認する。

**`/auto:issue` への組み込み**:

フェーズ連鎖の先頭に `investigate` フェーズを追加する。

```text
investigate(/think:investigate N)
  → design(/plan:design → design分commitの承認ゲート)
  → test → implement → docs → verify → review → ship
```

`phase-state.json` のフェーズ名一覧に `investigate` を追加する。

**`workflows.md` への追加**:

| 追加先 | 内容 |
| --- | --- |
| フェーズとコマンド表 | `事前確認`行に `investigate` を追記 |
| 自然言語ルーティング | 「事実確認して」「再現確認して」「ブランチ確認して」→ `/think:investigate` |

### 4.4. 既存コマンドとの区別

| コマンド | 対象 | やること |
| --- | --- | --- |
| `/think:clarify` | 依頼・仕様の曖昧さ | 完了条件・スコープの言語的整合を確認する |
| `/think:risks` | 変更のリスク | 後方互換・権限・手戻りの分類と深刻度付けをする |
| `/think:investigate` | Issue の事実 | main のコード・ブランチで「本当にある?」を検証する |

## 5. 失敗とロールバック

| ケース | 影響 | 対応 |
| --- | --- | --- |
| `gh issue view N` が失敗する(番号誤り・権限不足) | Issue 内容を読めない | エラーを表示して PM へ確認を求める |
| 調査対象ファイルが Issue 本文に明示されていない | コード照合の範囲が不明 | Issue 本文のキーワードから `grep` で推定し、推定根拠を調査レポートに明記する |
| `investigate` 追加で `auto:issue` のフェーズ数が増え既存の `phase-state.json` と非互換になる | 中断済み issue の再開時にフェーズ不整合が起きる | `investigate` は先頭フェーズのため、`completed` に `investigate` がない既存 `phase-state.json` は「investigate 未実施」として扱い、スキップして `design` から継続する(後方互換) |

## 6. 検証

| 層 | 検証内容 |
| --- | --- |
| 文書 | `docs/design/`のfrontmatter・目次・リンク・です・ます調を確認する |
| リンク | `investigate.md` から参照する `workflows.md` の節アンカーが正しいことを確認する |
| 既存検証 | `nix develop --command just verify` がグリーンであることを確認する |
| 動作確認 | `.claude/commands/think/investigate.md` のラッパー経由でコマンドが呼び出せることを会話内で確認する |

## 7. 未解決事項

| ID | 論点 | 決定者 | ブロックする作業 |
| --- | --- | --- | --- |
| U-01 | `auto:milestone` にも `investigate` を組み込むか | PM | milestone 単位の事実確認の要否 |
| U-02 | `features/ai-agent` テンプレートの `AGENTS.md` に `investigate` コマンドの案内を追記するか | Issue #116 相当 | 生成プロジェクトへの伝播 |
