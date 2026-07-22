# .claude/hooks

## 1. 概要

Claude Code hookイベントで実行するスクリプトを置くディレクトリです。他harnessに対応物がないClaude専用の実行機構です(Issue #114、Codexはinstruction-backedとして扱います)。

## 2. 責任

- `pre-push-verify.sh`: `PreToolUse`hook。`Bash`ツール呼び出しに`git push`が含まれる場合、
  `nix develop --command just verify`を実行し、失敗時はpushをブロックする

## 3. 責任外

- hookイベントの登録設定そのもの(`../settings.json`が持ちます)
