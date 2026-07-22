---
status: decided
---

# ADR: Goジェネレータ移行の採否

## 目次

- [1. コンテキスト](#1-コンテキスト)
- [2. 調査範囲](#2-調査範囲)
- [3. 実測結果](#3-実測結果)
- [4. 比較評価](#4-比較評価)
- [5. 決定](#5-決定)
- [6. 後続Issue候補](#6-後続issue候補)

## 1. コンテキスト

現行ジェネレータはPythonで実装され（`tooling/generator/`）、LOAD→RESOLVE→PLAN→RENDER→APPLYの
パイプラインとunit/E2Eテストが整備されています（348テスト）。Issue #111で複数ロール生成の
preflight問題が判明し、静的検査・単一バイナリ配布に利点があるGoへの移行価値を実測判断する
ためにIssue #112を設け、GoでPoC（`tooling/poc-go/`）を作成しました。

## 2. 調査範囲

Go PoCのスコープはIssue #112の完了条件に従い、以下の4ステージに限定しました。

| ステージ | 内容 |
| --- | --- |
| LOAD | `profile.toml` / `part.toml` のTOML読み込みと検証 |
| RESOLVE | Part依存解決・トポロジカルソート |
| PLAN | 変数束縛・ファイル一覧作成・衝突検出 |
| PREFLIGHT | 複数ロールの生成前検証（`--role`相当） |

RENDER/APPLYは実装せず、productionのentrypointは変更していません。

## 3. 実測結果

### 3.1. LOAD→RESOLVE→PLAN（ドライラン）の動作

```text
$ go run ./cmd/generate --name myapp --profile starter-cli --lang python --template-root ./template
LOAD: profile=starter-cli lang=python
  profile: starter-cli (cli)
  base parts: [base scale/small starter/cli features/ai-agent features/github-rulesets features/github-project]
  lang parts added: lang/python [starter/cli-python]
  loaded 8 part(s)
RESOLVE: topological sort
  [0] base
  [1] scale/small
  [2] starter/cli
  [3] features/ai-agent
  [4] features/github-rulesets
  [5] features/github-project
  [6] lang/python
  [7] starter/cli-python
PLAN: variable binding and file list
  planned 50 file(s)
  variables: map[project_name:myapp]
OK: LOAD→RESOLVE→PLAN completed successfully (dry-run, no files written)
```

### 3.2. 複数ロールpreflight

```text
$ go run ./cmd/generate --name myapp \
    --role backend:profile=starter-web-api,lang=python \
    --role frontend:profile=starter-cli,lang=go
PREFLIGHT: validating 2 role(s) for project "myapp"
  all 2 role(s) passed preflight validation
OK: preflight passed — no files written
```

未知プロファイル指定時は生成前にエラーを返し、ユーザーファイルへの影響なし:

```text
error: role "bad": unknown profile "no-such-profile". Available: starter-cli, ...
exit status 1
```

### 3.3. テスト実行

```text
$ go test ./... -v
ok  github.com/hisuilab/_template/poc-go/internal/loader    (7 tests)
ok  github.com/hisuilab/_template/poc-go/internal/planner   (3 tests)
ok  github.com/hisuilab/_template/poc-go/internal/preflight (5 tests)
ok  github.com/hisuilab/_template/poc-go/internal/resolver  (5 tests)
```

### 3.4. フォーマット・静的解析

```text
$ gofmt -l .     → 出力なし（全ファイルがgofmt準拠）
$ go vet ./...   → 出力なし（警告・エラーなし）
```

### 3.5. Python E2Eテストとの互換性比較

既存のblack-box E2E契約（`tests/e2e/test_generate_profiles.py`）はPython実装に対して348件全件パス。
Go PoCはPLANまでのドライランのため直接適用不可ですが、PlannerテストでPython版と同一条件の
アサーションを実施しています。

| 検証観点 | Python版 | Go PoC |
| --- | --- | --- |
| starter-cli + lang=python → 50ファイル計画 | E2Eで確認 | plannerテストで確認 |
| project_name変数の置換 | E2Eで確認 | plannerテストで確認 |
| lang省略時にsrc/main.pyが計画に含まれない | E2Eで確認 | plannerテストで確認 |
| 未知profileのpreflight拒否 | E2Eで確認 | preflightテストで確認 |
| 未知langのpreflight拒否 | E2Eで確認 | preflightテストで確認 |

### 3.6. Nix環境での再現性

Go 1.25がNixストア（`/nix/store/bzf2j0kapwnsnlf1r381zn08amcpp5k3-go-1.25.10/`）に存在し、
devShellの`flake.nix`には`pkgs.go`が宣言済みです（`lang/go`のPayload flake.nixも同様）。
`nix develop`環境から`go test ./...`・`go vet ./...`を再現可能に実行できます。
`tooling/poc-go/go.mod`に`github.com/BurntSushi/toml v1.4.0`の依存を1件追加しています。

### 3.7. 異常系の検証

| 異常系 | Go PoCの挙動 | ユーザーファイルへの影響 |
| --- | --- | --- |
| 存在しないprofile指定 | LoadError（利用可能一覧付き）を返してexit 1 | なし（ファイル生成前に停止） |
| 存在しないpart指定 | LoadError（利用可能一覧付き）を返してexit 1 | なし |
| 循環依存 | ResolveErrorを返してexit 1 | なし |
| 競合するpartの同時指定 | ResolveErrorを返してexit 1 | なし |
| --role内の未知profile/lang | PreflightError（全ロール検証後）を返してexit 1 | なし（生成前に停止） |

Go PoCはRENDER/APPLYを実装していないため、既存ユーザーファイルの変更・削除は構造上発生しません。

## 4. 比較評価

| 評価軸 | Python継続案 | Go移行案 |
| --- | --- | --- |
| **保守性** | 型注釈は実行時不強制。mypy追加で改善可能 | 静的型チェックがビルド時に強制される |
| **安全性** | テスト・型注釈で担保 | コンパイラによる型安全、nilpointerは検出が難しい |
| **外部依存** | Python, PYTHONPATH, questionary | Go toolchain + BurntSushi/toml + 対話UIは別途必要 |
| **配布** | Nix packageでラップ済み | 単一バイナリ（nix buildで自己完結） |
| **移行コスト** | ゼロ | LOAD〜PLANはPoC作成済み。RENDER/APPLY/wizard/workspaceは未実装 |
| **二重保守期間** | なし | 移行完了まで発生 |
| **AIエージェント保守** | formatter(ruff)/linter/testが明確 | gofmt/go vet/go testが明確 |
| **既存テスト資産** | 348件そのまま利用可能 | Go版に書き直しが必要（E2EはPythonから実行可能） |
| **対話UI(wizard)** | questionaryで実装済み | 未着手（PTY操作が複雑） |
| **build/test手順** | `pytest` / `ruff` | `go test` / `gofmt` / `go vet` |

### 4.1. 移行の主なコスト

- RENDER/APPLY（ステージング書き込み・原子的コピー）の実装
- wizard（対話UI）の実装（go-promptやbubbletea等の依存追加が必要）
- workspace初期化サブコマンドの実装
- 348件のPython E2EテストをGoまたはbatsへ書き直し
- 二重保守期間（PythonとGoの並行運用）

### 4.2. Go移行の利点

- 静的型チェックがビルド時に強制される（Pythonの型注釈は実行時不強制）
- 単一バイナリで配布可能（`nix build`で自己完結）
- entrypointの依存がGoのみ（Python + PYTHONPATH + questionaryが不要）
- `go test` / `gofmt` / `go vet`の手順がAIエージェントにとって明確

## 5. 決定

**Go移行を採用する（段階的）。** ただし、今回のPoCの実測で以下の条件を確認しました。

1. LOAD→RESOLVE→PLANの移植は技術的に実現可能であり、PoCで実証済みです
2. RENDER/APPLY/wizard/workspaceは残存しており、全面移行には追加Issueが必要です
3. 移行期間中はPython実装を維持し、production entrypointは切り替えを行いません
4. wizard（対話UI）の移植コストが最大のリスクです

> [!NOTE]
> Python実装の責務分離、production entrypointの切り替え、wizard移植、
> Python実装の削除は採用決定後の別Issueとします。

## 6. 後続Issue候補

| Issue候補 | 内容 |
| --- | --- |
| Go RENDER/APPLY実装 | staging書き込み・原子的コピー・manifest書き込みの実装 |
| Go wizard実装 | 対話UI（questionary相当）の移植 |
| Go workspace実装 | init-workspaceサブコマンドの移植 |
| Python entrypoint切り替え | Go版をproduction entrypointへ昇格 |
| Python実装の削除 | `tooling/generator/`の削除とtest資産の移行 |
