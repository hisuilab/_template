---
status: implemented
issue: 43
created_at: 2026-07-13
---

# Design Proposal: `just new` / `create` / `generate` UX 統一

## 背景

Issue #13（init-workspace）と Issue #16（create ウィザード）の実装後、`just new` は
フル対話型ウィザードのみに対応していた。以下の問題が残っていた:

1. `just new test` がエラー（just が `test` をレシピ名と解釈）
2. `generate --name` と `--output` の責務が分離しており関係が不明瞭
3. ウィザードをスキップして非対話的に生成する手段がない

## 完了条件

- [x] `just new` → フルウィザード（現状と同じ動作）
- [x] `just new myapp` → name 事前入力済みウィザード（lang/profile のみ選択）
- [x] `just new myapp --lang python --profile small-cli` → 完全非対話で即生成
- [x] `just new myapp --output ./myapp` → worktree 追加（`./myapp/myapp/` に生成）
- [x] `generate` の `--output` の意味を「親ディレクトリ」に変更、省略時は `{cwd}/{name}/{name}-main`
- [x] 既存テストがすべて通る
- [x] `just new test` がエラーにならない（Justfile のレシピ名誤解釈を解消）

## 設計

### 出力パスのルール

| 呼び出し | 生成先 | `project_name` |
| --- | --- | --- |
| `--output` なし | `./{name}/{name}-main/` | `name` |
| `--output ./myapp` | `./myapp/{name}/` | `name` |

`-main` サフィックスは「新規プロジェクトのメイン worktree」を表す自動導出規則。
`--output` 指定時は呼び出し元が親ディレクトリを管理しているとみなし付与しない。

### `create` コマンド — 引数追加

```text
python3 -m tooling.generator create [NAME] [--lang LANG]
                                    [--profile PROFILE] [--output DIR]
```

- `NAME` は省略可能な positional 引数（`just new myapp` のように positional で渡す）
- 引数が渡された項目はウィザードの対応する質問をスキップ
- 全引数が揃った場合はウィザードを完全スキップして `generate` と同等の動作
- `--output` は親ディレクトリ（省略時は `.`）

### `generate` コマンド — インタフェース変更

```text
# 変更前
generate --name NAME --profile PROFILE --output FULL_PATH --lang LANG

# 変更後
generate --name NAME --profile PROFILE [--output PARENT_DIR] --lang LANG
```

- `--output` は**親ディレクトリ**（省略時は `.`）に変更
- 実際の生成先 = `{output}/{name}-main/`（`--output` なし）または `{output}/{name}/`（あり）
- `GenerateRequest.output_path` は引き続き最終生成先のフルパスを保持（内部実装は変えない）

### `just new` — workspace justfile 変更

```justfile
# 変更前
new:
    nix run github:hisuilab/_template -- create

# 変更後
new *args:
    nix run github:hisuilab/_template -- create {{args}}
```

### ウィザードの質問フロー変更

```text
# 現在
Project name:          → テキスト入力
Output path [./x/x-main]:  → テキスト入力（スキップ可）
Language:              → 選択
Profile:               → 選択

# 変更後
Project name:          → テキスト入力（--name 指定時スキップ）
Language:              → 選択（--lang 指定時スキップ）
Profile:               → 選択（--profile 指定時スキップ）
→ 生成先: ./name/name-main/  を確認表示して生成
```

`Output path` の質問を廃止し、生成先は確認表示のみとする。
worktree 追加は `--output` フラグで対応。

## 実装計画

### Step 1: `generate` コマンドの `--output` セマンティクス変更

- `cli.py`: `_cmd_generate` の output パス計算を変更
  - `--output` 未指定: `Path.cwd() / name / f"{name}-main"`
  - `--output` 指定: `Path(args.output) / name`
- `models.py`: `GenerateRequest` の変更なし（`output_path` は最終パスのまま）
- 影響テスト: `test_generator.py`、`test_generate_profiles.py` の output 関連ケース修正

### Step 2: `create` コマンドへの引数追加

- `cli.py`: `create` サブコマンドに `--name` / `--lang` / `--profile` / `--output` を追加
- `wizard.py`: `run_wizard(prefill)` として prefill 引数を受け取り、渡された項目の質問をスキップ
- `Output path` 質問を廃止、生成先は `print` で確認表示のみ

### Step 3: workspace justfile 変更

- `template/workspaces/default/justfile`: `new *args:` に変更

### Step 4: テスト追加

- `test_generator.py`: `--output` 省略時のデフォルトパス、`--output` 指定時のパス
- `test_generate_profiles.py`: `--output` なし生成の e2e テスト
- `test_wizard.py`: prefill ありウィザードのスキップ動作

## 未解決事項

- `generate` の `--output` セマンティクス変更は破壊的変更。既存の利用箇所（テスト含む）を
  すべて更新する必要がある
- `just new myapp --output ./myapp` の `--output` は just の引数解析上 `*args` に含まれる
  ため `nix run ... -- create myapp --output ./myapp` として正しく渡る想定（要確認）
