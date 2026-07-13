---
status: implemented
proposed_at: 2026-07-13
approved_at: 2026-07-13
approved_by: PM
approval_ref: "https://github.com/hisuilab/_template/pull/20"
implemented_at: 2026-07-13
related: "#16"
---

# 設計提案: create サブコマンド追加（対話型プロジェクト生成ウィザード）

## 目次

- [1. 問題](#1-問題)
- [2. 対象範囲](#2-対象範囲)
- [3. 選択肢](#3-選択肢)
- [4. 設計案](#4-設計案)
- [5. 失敗とロールバック](#5-失敗とロールバック)
- [6. 検証](#6-検証)
- [7. 未解決事項](#7-未解決事項)

## 1. 問題

`generate` サブコマンドはフラグを明示して呼び出す非対話型インターフェースです。初めて使うユーザーや複数人チームには摩擦があり、vite / create-react-app のような対話型ウィザードが必要です。

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| `tooling/generator/wizard.py` モジュール追加 | `generate` サブコマンドの変更 |
| `cli.py` への `create` サブコマンド追加 | Parts システム（resolver/planner）の変更 |
| `flake.nix` への `questionary` 依存追加 | `init-workspace` の変更 |
| `template/workspaces/default/justfile` の `new` レシピ更新 | 他の workspace テンプレート |

## 3. 選択肢

実装言語・ライブラリは確定済み（Issue #16 本文参照）。Python + `questionary 2.1.1`（nixpkgs-25.11 収録）を採用します。

## 4. 設計案

### ファイル構成

```text
tooling/generator/
└── wizard.py       # WizardAnswers + run_wizard()（新規）

template/workspaces/default/
└── justfile        # new レシピを create 呼び出しに変更
```

### `wizard.py` 責務

1. `WizardAnswers` データクラスを定義する（name / output / lang / profile）
2. `run_wizard(available_langs, available_profiles)` で questionary プロンプトを順に表示し `WizardAnswers` を返す
3. 出力パスのデフォルトは `./name/name-main`（worktree 運用想定）

### CLI インターフェース

```sh
nix run .# -- create
```

引数なし。ウィザードがすべての入力を担当します。

```text
? Project name: my-app
? Output path [./my-app/my-app-main]: _
? Language:  ❯ python
               typescript
? Profile:   ❯ small-cli
               small-web-api
               small-library
→ Generating at ./my-app/my-app-main...
```

### `flake.nix` の変更

`runtimeInputs` を `questionary` 入りの Python 環境に変更します。

```nix
runtimeInputs = [ (pkgs.python3.withPackages (ps: [ ps.questionary ])) ];
```

devShell にも `pkgs.python3Packages.questionary` を追加します。

### `template/workspaces/default/justfile` の変更

```justfile
new:
    nix run github:hisuilab/_template -- create
```

### 依存方向

```text
cli.py
  └── tooling.generator.wizard (新規)
        └── questionary（外部ライブラリ）
```

`wizard.py` は `loader` / `planner` 等に依存しません。`_cmd_create` が `WizardAnswers` を受け取って `_cmd_generate` を呼びます。

## 5. 失敗とロールバック

| ケース | 影響 | 対応 |
| --- | --- | --- |
| TTY なし環境での実行（CI 等） | questionary がエラー終了 | `create` は対話型専用とし、非対話用途は `generate` を継続使用 |
| questionary が nixpkgs に存在しない | nix build 失敗 | `questionary 2.1.1` が nixos-25.11 収録済みであることを確認済み |

## 6. 検証

| 層 | 検証内容 |
| --- | --- |
| `tests/unit/test_flake.py` | `cli.py` に `create` サブコマンドが存在する（文字列マッチ） |
| `tests/unit/test_wizard.py`（新規） | `run_wizard` が questionary をモックして `WizardAnswers` を正しく返す |

## 7. 未解決事項

なし（すべての論点が解消済み）。
