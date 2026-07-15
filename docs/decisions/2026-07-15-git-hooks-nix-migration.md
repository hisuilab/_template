---
status: approved
proposed_at: 2026-07-15
approved_at: 2026-07-15
approved_by: PM
approval_ref: "issue-76"
implemented_at: 2026-07-15
related: "2026-07-15-nix-in-docker-devcontainer"
---

# 意思決定の記録: pre-commit フック管理を prek から git-hooks.nix へ移行

## 目次

- [1. 背景と問題](#1-背景と問題)
- [2. 検討した選択肢](#2-検討した選択肢)
- [3. 採用案](#3-採用案)
- [4. 理由](#4-理由)
- [5. トレードオフと影響](#5-トレードオフと影響)

## 1. 背景と問題

`nix develop` 外の環境（例: MacBook Air で `nix develop` に入らない状態）でコミットしようとしたとき、`.git/hooks/pre-commit` が Python ベースの `prek` を PATH から探すため失敗していた。`prek` は Python 製ツールであり、PATH に `python3` がない環境では動作しない。

生成プロジェクトのテンプレートも同じ問題を抱えていた。

## 2. 検討した選択肢

| # | 選択肢 |
| --- | --- |
| A | `git-hooks.nix`（cachix/git-hooks.nix）へ移行 |
| B | prek のまま、`nix develop` に入ることを必須ルールとする |
| C | `.git/hooks/pre-commit` を PATH に依存しない独自シェルスクリプトに書き換える |

## 3. 採用案

A: git-hooks.nix へ移行

## 4. 理由

- `git-hooks.nix` は `devShell.shellHook` が `.git/hooks/pre-commit` を `/nix/store/…` の絶対パスで生成するため、`nix develop` に入っていない状態でも Nix がインストールされていればフックが動作する
- `convco`（Conventional Commits バリデータ）が nixpkgs に存在し、Python 製の `conventional-pre-commit` を置き換えられる
- treefmt-nix と同様に flake.nix 上で宣言的に管理でき、バージョンが `flake.lock` で固定される

## 5. トレードオフと影響

| 観点 | 内容 |
| --- | --- |
| 改善 | `nix develop` 外でもコミット可能。Python が PATH 不要 |
| 変更 | `.pre-commit-config.yaml` は `shellHook` が nix store へのシンボリックリンクとして自動生成。git 管理から除外 |
| 削除 | `scripts/precommit`（prek ラッパー）、`tests/unit/scripts/precommit.bats` を削除 |
| 残存制約 | Nix 自体（`/nix/store`）はマシンにインストールされている必要がある。Windows ネイティブは非対応 |
