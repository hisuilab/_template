# docs

## 1. 概要

本リポジトリ（`_template`）の要件・アーキテクチャ・設計・開発手順を置くディレクトリです。

## 2. 責任

| ディレクトリ | 正本とする問い |
| --- | --- |
| [`requirements/`](requirements/) | 何を作るか（利用者・価値・対象範囲） |
| [`architecture/`](architecture/) | どう作るか（Part 構成・モジュール責務・依存方向） |
| [`design/`](design/) | Issue 単位の設計提案 |
| [`milestones/`](milestones/) | どの順序で作るか（完了条件・進捗） |
| [`decisions/`](decisions/) | なぜその方式を選んだか（非自明な判断の記録） |
| [`development/`](development/) | 開発手順・文書ポリシー・リポジトリ設定 |
| [`draft/`](draft/) | プロトタイプ作業文書（廃止予定） |

## 3. 責任外

- 実装コード（`tooling/`・`template/` が持ちます）
- AI エージェントのワークフロー・権限定義（`.claude/rules/` が持ちます）
