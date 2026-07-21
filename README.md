# _TEMPLATE

[![git-hooks.nix](https://img.shields.io/badge/git--hooks-nix-5277C3?logo=nixos&logoColor=white)](https://github.com/cachix/git-hooks.nix)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196?logo=conventionalcommits&logoColor=white)](https://conventionalcommits.org)

## 目次

- [\_TEMPLATE](#_template)
  - [目次](#目次)
  - [1. 概要](#1-概要)
  - [2. クイックスタート](#2-クイックスタート)
  - [3. 構成](#3-構成)

## 1. 概要

新規プロジェクトの雛形を生成するためのテンプレートリポジトリです。Nix flakeによる再現可能な開発環境と、treefmt(整形)・pre-commitによるフォーマット/lint/シークレット検査のゲート、justタスクランナー、batsによるテストを備えています。`tooling/`のジェネレータが`template/`のProfileを元に新規プロジェクト一式を生成します。

## 2. クイックスタート

### Nix 環境（macOS / Linux）

```sh
nix develop   # devShellを有効化(direnv利用時は `direnv allow` でも可)
just verify   # test + lint(format) + check-docs
```

### devcontainer（Windows / Nix 未経験者）

Docker と VS Code がインストールされていれば Nix 不要で開発できます。

1. VS Code でリポジトリを開く
2. コマンドパレット →「Reopen in Container」
3. コンテナ起動後、ターミナルで `nix develop` に入ると git フックが自動インストールされます

```sh
nix develop          # devShell に入る（初回は nix store のダウンロードに数分かかります）
just verify          # test + lint + check-docs
```

### ワークスペースの初期化（初回のみ）

`~/Projects` に `flake.nix`・`.envrc`・`justfile` を配置します。`~/Projects` が存在しない場合は自動作成されます。

```sh
nix run github:hisuilab/_template -- init-workspace --path ~/Projects
direnv allow ~/Projects
```

ローカルの `_template` リポジトリから実行する場合、または `just` で実行する場合:

```sh
just init-workspace               # デフォルト: ~/Projects
just init-workspace path=~/Work   # パスを変える場合
```

### 新規プロジェクトの生成

ワークスペース初期化後は `just new` でプロジェクトを対話的に作成できます。

```sh
cd ~/Projects
just new                          # 対話ウィザードで生成
just new myapp                    # 名前を事前入力してウィザード起動
```

`just new` は `nix run github:hisuilab/_template -- create` を呼び出します。ウィザードを使わずに直接生成する場合:

```sh
nix run github:hisuilab/_template -- generate \
  --name <project-name> \
  --profile starter-cli \
  --lang python \
  --output ~/Projects/<project-name>
```

生成後はプロジェクトディレクトリに移動してセットアップします。

```sh
cd ~/Projects/<project-name>
nix develop --command just init   # git 初期化とフックのインストール（初回のみ）
nix develop                       # 開発シェルに入る
just verify                       # 動作確認
```

利用可能なProfileは`starter-cli`、`starter-web-api`、`starter-library`、`starter-web-htmx`、利用可能な`--lang`は`python`、`typescript`、`rust`、`go`です。`--lang`を省略すると、言語別の実装(`src/main.py`等)を含まないlang非依存の骨格のみが生成されます。技術選定が未確定な段階で先にプロジェクトの土台だけ作りたい場合はこの形で生成し、確定後に`just inject lang/python`のようにPartを後から追加できます。

## 3. 構成

| ディレクトリ | 内容 |
| --- | --- |
| [scripts/](scripts/README.md) | 開発環境の補助スクリプト |
| [tests/](tests/README.md) | ユニット/結合/E2Eテスト |
| [tooling/](tooling/README.md) | プロジェクト生成ジェネレータ |
| [template/](template/README.md) | ジェネレータが読み込むProfile定義 |
| [docs/](docs/README.md) | 生成先プロジェクトに配布する文書規約(未着手) |
