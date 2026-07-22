# .claude/commands

## 1. 概要

Claude Codeのスラッシュコマンド起動定義を置くディレクトリです。各ファイルは`agent-workflow/commands/`の対応するファイルを読み、その指示に従う薄いラッパーです。

## 2. 責任

- `status.md`・`verify.md`: フェーズに紐付かない横断コマンド
- `think/`・`plan/`・`build/`・`review/`・`ship/`・`verify/`・`auto/`・`template/`: フェーズ別サブディレクトリ

## 3. 責任外

- コマンドの実行契約の内容そのもの(`agent-workflow/commands/`が持ちます)
