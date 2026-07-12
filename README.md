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

新規プロジェクトを生成するには、nix devShell内で次のコマンドを実行します。

```sh
python3 -m tooling.generator generate \
  --name <project-name> \
  --profile small-cli \
  --output ~/Projects/<project-name>
```

利用可能なProfileは`small-cli`、`small-web-api`、`small-library`です。

## 3. 構成

| ディレクトリ | 内容 |
| --- | --- |
| [scripts/](scripts/README.md) | 開発環境の補助スクリプト |
| [tests/](tests/README.md) | ユニット/結合/E2Eテスト |
| [tooling/](tooling/README.md) | プロジェクト生成ジェネレータ |
| [template/](template/README.md) | ジェネレータが読み込むProfile定義 |
| [docs/](docs/README.md) | 生成先プロジェクトに配布する文書規約(未着手) |
