# .codex/hooks

## 1. 概要

Codexのhookイベントで実行するスクリプトを置くディレクトリです。`.claude/hooks/`のCodexアダプター版で、実行内容は同一です。

## 2. 責任

- `pre-push-verify.sh`: `PreToolUse`hook。`Bash`ツール呼び出しに`git push`が含まれる場合、
  `nix develop --command just verify`を実行し、失敗時はpushをブロックする

## 3. 責任外

- hookイベントの登録設定そのもの(`../hooks.json`が持ちます)

## 4. 既知の制約

Codex側は環境・セッションごとに`/hooks`での明示的なtrustが必要です(初回のみ)。trustされるまで、このhookは発火しません。
