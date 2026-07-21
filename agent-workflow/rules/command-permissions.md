# Command Permissions / コマンド権限

コマンドの副作用を実行前に判断できるように、権限レベル、承認条件、subagentへ委譲できる
範囲を定義します。`.claude/commands/`の権限宣言の正本です。

## 目次

- [1. 権限レベル](#1-権限レベル)
- [2. 承認ルール](#2-承認ルール)
- [3. subagent境界](#3-subagent境界)
- [4. コマンドヘッダ](#4-コマンドヘッダ)
- [5. コマンド一覧](#5-コマンド一覧)

## 1. 権限レベル

権限レベルはコマンドが実行してよい最大の副作用を示します。上位レベルは下位の操作を含みます。

| レベル | 許可する操作 | 例 |
| --- | --- | --- |
| `read-only` | ファイル・Git状態の読み取りと画面出力のみ | `/status` |
| `tmp-write` | `tmp/`配下へのレポート・計画・状態ファイルの書き込み | `/verify`、`/verify:handoff`、`/review:code` |
| `docs-write` | 文書ファイルの作成・更新 | (現在該当コマンド無し) |
| `source-write` | 実装・テスト・設定の作成・更新 | `/build:test`、`/build:implement` |
| `git-commit` | `git add` / `git commit`、ローカルブランチ作成 | `/plan:requirements`・`/plan:architecture`(`project-direction.md`差分のcommit)、`/plan:design`(design分のcommit)、`/build:docs`(未commit差分をtest→feat→docsへ分割して連続commit)、`/ship:pr`のcommit段階(Production Mode) |
| `external-write` | push、PR作成など外部状態の変更 | `/ship:pr`のpush/PR段階(Production Modeのみ)、`/auto:issue`(Production Mode)、`/plan:issue`(GitHub Issue作成) |

## 2. 承認ルール

| 操作 | 承認 |
| --- | --- |
| `read-only` / `tmp-write` | 不要です |
| `docs-write` | フェーズ完了時に確認します |
| `source-write` | マイルストーン/Issue・設計の範囲内で自走します。ただしcommitは行いません |
| `git-commit` | 実行直前に差分とcommit messageを提示します(`/build:docs`は複数commit分をまとめて1回提示します) |
| `external-write` | 実行直前に明示承認を得ます |
| 依存関係の追加・更新 | 実行前に明示承認を得ます |
| 破壊的Git操作、force push、Secret、Release | 実行前に明示承認を得ます |

## 3. subagent境界

- subagentへ渡す標準権限は`read-only`または`tmp-write`です
- subagentは意思決定の問い合わせとsubagentの再帰呼び出しを行いません
- `tmp-write`を超える状態変更は、subagentの報告を受けたトップレベルコマンドが自身の
  権限宣言の範囲で行います

## 4. コマンドヘッダ

全コマンドは冒頭で次の6行を宣言します(`管理責任`〜`状態確認先`は今回追加した拡張、
`権限`〜`承認`は既存踏襲)。

```text
管理責任: <このコマンドが作成・更新する成果物を1文で>
ワークフロー: <think|plan|build(docs)|build(test)|run(red)|build(impl)|run(green)|review|ship のどこか>
状態確認先: <進行状況・完了条件の正本ファイルパス>

権限: `<レベル>`
副作用: <生じる変更の要約>
承認: <承認が必要なタイミング。不要なら「不要です」>
```

続けて「読み込む文書」節で、対象ディレクトリのREADME.mdを含む必読文書を列挙します
(ディレクトリの責任範囲説明はREADME.md自身が正本のため、コマンド側で複製しません)。

## 5. コマンド一覧

| コマンド | 権限 | 主な副作用 |
| --- | --- | --- |
| `/status` | read-only | なし |
| `/verify` / `/verify:handoff` | tmp-write | 検証レポート |
| `/review:design` / `/review:code` / `/review:docs` / `/review:test` / `/review:security` / `/review:audit` | tmp-write | `tmp/milestone-{N}/` または `tmp/issue-{N}/` 配下のレビューレポート |
| `/think:clarify` / `/think:risks` | read-only | なし |
| `/plan:requirements` / `/plan:architecture` | git-commit | `project-direction.md`更新+その差分のcommit |
| `/plan:milestone` | git-commit | `m{N}-slug`ブランチ作成+`tmp/milestone-{N}/phase-state.json`初期化 |
| `/plan:issue` | external-write | GitHub Issue作成+`type/issue-N-topic`ブランチ作成+`tmp/issue-{N}/phase-state.json`初期化 |
| `/plan:design` | git-commit | マイルストーン文書/設計提案の作成+design分のcommit |
| `/build:docs` | git-commit | README・マイルストーン文書・draft・decisions更新+未commit差分の複数commitへの分割実行 |
| `/build:test` / `/build:implement` | source-write | テスト・実装(commitしない) |
| `/ship:readiness` | tmp-write | 出荷判定レポート |
| `/ship:pr` | git-commit(Prototype) / external-write(Production) | Prototype: `prototype`へのfast-forward merge。Production: commit・push・PR作成 |
| `/auto:milestone` | git-commit(Prototype) | マイルストーンのフェーズ連鎖実行(承認ゲートあり)。副作用は連鎖先の各コマンドに従う |
| `/auto:issue` | external-write(Production) | IssueのEフェーズ連鎖実行(承認ゲートあり)。副作用は連鎖先の各コマンドに従う |
| `/template:generate` | read-only | なし(未実装スタブ) |
