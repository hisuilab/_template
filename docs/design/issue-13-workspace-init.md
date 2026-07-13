---
status: implemented
proposed_at: 2026-07-13
approved_at: 2026-07-13
approved_by: PM
implemented_at: 2026-07-13
related: "#13"
---

# 設計提案: init-workspace サブコマンド追加（~/Projects 親環境の整備）

## 目次

- [1. 問題](#1-問題)
- [2. 対象範囲](#2-対象範囲)
- [3. 選択肢](#3-選択肢)
- [4. 設計案](#4-設計案)
- [5. 失敗とロールバック](#5-失敗とロールバック)
- [6. 検証](#6-検証)
- [7. 未解決事項](#7-未解決事項)

## 1. 問題

`~/Projects` 配下でどこからでも `just`・`nix` を使えるようにしたい。現状は各プロジェクトの `nix develop` に入らないと利用できない。[2026-07-13-workspace-init-subcommand.md](../decisions/2026-07-13-workspace-init-subcommand.md) で `init-workspace` サブコマンドをジェネレータ CLI へ追加する方針が決定済み。

## 2. 対象範囲

| 対象 | 対象外 |
| --- | --- |
| `cli.py` への `init-workspace` サブコマンド追加 | `generate` サブコマンドの変更 |
| `template/workspaces/default/` 固定テンプレートの作成 | Parts システム（resolver/planner）の変更 |
| `tooling/generator/workspace.py` モジュール追加 | `~/Projects` への自動インストール |

## 3. 選択肢

アーキテクチャ設計済み（[Decision Record](../decisions/2026-07-13-workspace-init-subcommand.md) 参照）。選択は確定。

## 4. 設計案

### ファイル構成

```text
tooling/generator/
├── cli.py         # init-workspace サブコマンドを追加
└── workspace.py   # init-workspace ロジック（新規）

template/workspaces/
└── default/
    ├── flake.nix         # minimal devShell（just・git・direnv）
    ├── dot-envrc         # use flake
    └── justfile          # new レシピ（nix run ... generate を呼ぶ）
```

### CLI インターフェース

```sh
nix run .# -- init-workspace --path ~/Projects [--workspace default]
```

- `--path`: 初期化する親ディレクトリ（必須）
- `--workspace`: 使用するワークスペーステンプレート名（デフォルト: `default`）
- 対象パスが既存かつ `flake.nix` が存在する場合はエラー終了（上書き不可）

### `workspace.py` 責務

1. `WORKSPACE_ROOT / workspace_name / *` を読み込む（`WORKSPACE_ROOT` は `TEMPLATE_ROOT` と同列に env var で注入可能）
2. `dot-` プレフィックス除去（planner の同等ロジックを利用）
3. renderer → applier で出力先に適用
4. `nix flake update --flake <dest>` を実行して `flake.lock` を生成する

Parts システム（loader / resolver / planner）は使用しない。

### 生成ファイル内容

**`flake.nix`**:

```nix
{
  description = "Projects workspace";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
  outputs = { self, nixpkgs, ... }:
    let
      systems = ["aarch64-darwin" "aarch64-linux" "x86_64-darwin" "x86_64-linux"];
      forAllSystems = nixpkgs.lib.genAttrs systems;
      pkgsFor = system: nixpkgs.legacyPackages.${system};
    in {
      devShells = forAllSystems (system:
        let pkgs = pkgsFor system;
        in { default = pkgs.mkShell { packages = [ pkgs.just pkgs.git ]; }; });
    };
}
```

**`.envrc`**: `use flake`

**`justfile`**:

```justfile
# new name [lang=python] [output=]
# output のデフォルト: {{name}}/{{name}}-main（worktree 運用を想定）
# 例: just new my-app
#     just new my-app lang=typescript
#     just new my-app output=my-app/prototype
new name lang="python" output="":
    #!/usr/bin/env bash
    set -euo pipefail
    dest="{{output}}"
    if [ -z "$dest" ]; then dest="{{name}}/{{name}}-main"; fi
    nix run github:hisuilab/_template -- generate \
        --name "{{name}}" \
        --profile small-cli \
        --lang "{{lang}}" \
        --output "$dest"
```

**`flake.lock`**: `workspace.py` が `nix flake update` を実行して生成する（テンプレートには含めない）

### 依存方向の変化

```text
cli.py
  ├── tooling.generator.workspace (新規)
  │     ├── tooling.generator.renderer（再利用）
  │     └── tooling.generator.applier（再利用）
  └── (既存) tooling.generator.loader 等
```

`workspace.py` は `loader` / `resolver` / `planner` に依存しない。

## 5. 失敗とロールバック

| ケース | 影響 | 対応 |
| --- | --- | --- |
| 対象パスが既存 | 上書きリスク | `flake.nix` 存在チェックでエラー終了 |
| `WORKSPACE_ROOT` 未設定 | `template/workspaces/` が見つからない | `TEMPLATE_ROOT` と同じ env var 注入パターンを適用 |
| 書き込み失敗 | 部分出力 | applier の staging → 出力先コピーで失敗時クリーンアップ |
| `nix flake update` 失敗 | `flake.lock` が生成されない | エラーを表示し「`nix flake update` を手動実行してください」と案内する。ファイル自体は生成済みのため再実行不要 |

## 6. 検証

| 層 | 検証内容 |
| --- | --- |
| `tests/unit/test_flake.py` | `init-workspace` サブコマンドが CLI に存在する（文字列マッチ） |
| `tests/unit/test_workspace.py`（新規） | `workspace.py` が `dot-` 除去・renderer・applier を正しく組み合わせる |
| `tests/e2e/test_workspace.py`（新規） | `init-workspace --path <tmpdir>` で 3 ファイルが生成される |

## 7. 未解決事項

なし（すべての論点が解消済み）。
