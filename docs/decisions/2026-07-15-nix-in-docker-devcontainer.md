---
status: approved
proposed_at: 2026-07-15
approved_at: 2026-07-15
approved_by: PM
approval_ref: "issue-78"
implemented_at: 2026-07-15
related: "2026-07-15-git-hooks-nix-migration"
---

# 意思決定の記録: devcontainer に Nix-in-Docker を採用

## 目次

- [1. 背景と問題](#1-背景と問題)
- [2. 検討した選択肢](#2-検討した選択肢)
- [3. 採用案](#3-採用案)
- [4. 理由](#4-理由)
- [5. トレードオフと影響](#5-トレードオフと影響)

## 1. 背景と問題

Windows ユーザーが過半数を占める、または Nix に導入障壁があるチームでは、`nix develop` を全員に要求するのが現実的でない。Windows ネイティブでは `/nix/store` が存在せず、git-hooks.nix が生成するフックも動作しない。

## 2. 検討した選択肢

| # | 選択肢 |
| --- | --- |
| A | devcontainer で Nix をコンテナ内に閉じ込める（Nix-in-Docker） |
| B | devcontainer で Nix を使わず、ツールを Dockerfile で直接インストールする |
| C | WSL2 + Nix を Windows ユーザーに要求する |

## 3. 採用案

A: Nix-in-Docker（`ghcr.io/devcontainers/features/nix:1` feature でコンテナ内に Nix を透過的に提供）

## 4. 理由

- ユーザーが意識するのは「Docker + VS Code のみ」であり、Nix の知識が不要
- コンテナ内でも `flake.lock` によるバージョン固定が効き、B 案のような `flake.lock` との二重管理が発生しない
- `postCreateCommand: nix develop --command echo 'devShell ready'` が shellHook を呼び出し、git フックを自動インストールする
- 既存の `flake.nix`・フック設定を変更せず、devcontainer レイヤーを上乗せするだけで完結する

B 案はシンプルだが、nixpkgs のバージョン管理と Dockerfile のバージョン管理が分離して乖離が起きやすい。C 案は WSL2 の習熟コストが残る。

## 5. トレードオフと影響

| 観点 | 内容 |
| --- | --- |
| 改善 | Windows ユーザーが Docker + VS Code のみで開発・コミット可能 |
| 改善 | チームの OS 多様性に対応しつつ、再現性（flake.lock ピン）を維持 |
| 制約 | Docker のインストールが必要（Docker Desktop または Docker Engine） |
| 制約 | 初回 `nix develop` に数分かかる（nixpkgs ダウンロード）。GitHub Actions GHA キャッシュで軽減 |
| 対象外 | Docker を使えない環境（社内プロキシ制限等）は別途検討が必要 |
