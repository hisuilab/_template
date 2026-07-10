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

新規プロジェクトの雛形を生成するためのテンプレートリポジトリです。Nix flakeによる再現可能な開発環境と、treefmt(整形)・prek(pre-commit)によるフォーマット/lint/シークレット検査のゲート、justタスクランナー、batsによるテストを備えています。`tooling/`のジェネレータが`template/`のProfileを元に新規プロジェクト一式を生成する構想ですが、現時点では開発環境の基盤のみ実装済みです。

## 2. クイックスタート

```sh
nix develop   # devShellを有効化(direnv利用時は `direnv allow` でも可)
just verify   # test + lint(format) + check-docs
```

## 3. 構成

| ディレクトリ | 内容 |
| --- | --- |
| [scripts/](scripts/README.md) | 開発環境の補助スクリプト |
| [tests/](tests/README.md) | ユニット/結合/E2Eテスト |
| [tooling/](tooling/README.md) | プロジェクト生成ジェネレータ(未着手) |
| [template/](template/README.md) | ジェネレータが読み込むProfile(未着手) |
| [docs/](docs/README.md) | 生成先プロジェクトに配布する文書規約(未着手) |
| [src/](src/README.md) | 用途未確定 |
