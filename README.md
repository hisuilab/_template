# _TEMPLATE

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
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

```sh
nix develop   # devShellを有効化(direnv利用時は `direnv allow` でも可)
just verify   # test + lint(format) + check-docs
```

新規プロジェクトを生成するには、次のコマンドを実行します。`_template` ディレクトリにいなくても呼び出せます。

```sh
nix run github:hisuilab/_template -- generate \
  --name <project-name> \
  --profile starter-cli \
  --lang python \
  --output ~/Projects/<project-name>
```

またはローカルの `_template` リポジトリから実行する場合:

```sh
nix run .# -- generate \
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

利用可能なProfileは`starter-cli`、`starter-web-api`、`starter-library`、利用可能な`--lang`は`python`、`typescript`です。

## 3. 構成

| ディレクトリ | 内容 |
| --- | --- |
| [scripts/](scripts/README.md) | 開発環境の補助スクリプト |
| [tests/](tests/README.md) | ユニット/結合/E2Eテスト |
| [tooling/](tooling/README.md) | プロジェクト生成ジェネレータ |
| [template/](template/README.md) | ジェネレータが読み込むProfile定義 |
| [docs/](docs/README.md) | 生成先プロジェクトに配布する文書規約(未着手) |
