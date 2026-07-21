# .claude

## 1. 概要

Claude Code固有の実行機構(スラッシュコマンド・subagent定義・Skill・hook・共有設定)を置くディレクトリです。ワークフローの内容そのもの(harness非依存の決めごと)は`agent-workflow/`が正本で、ここは薄いアダプターです(Issue #114)。

## 2. 責任

- `commands/`: スラッシュコマンドの起動定義(`agent-workflow/commands/`を参照する薄いラッパー)
- `agents/`: subagent定義(`tools:`/`model:`等Claude固有フィールド、`agent-workflow/agents/`を参照)
- `skills/`: Skillの自動発火定義(`agent-workflow/skills/`を参照)
- `hooks/`: Claude Code hookイベントのスクリプト(Claude専用、他harness対応物なし)
- `settings.json`: 開発者間で共有するClaude Code設定(hook配線等、秘密情報を含まない)

## 3. 責任外

- ワークフローの内容そのもの(`agent-workflow/`が持ちます)
- 個人のローカル設定・セッション状態(`settings.local.json`・`scheduled_tasks.lock`、非追跡のまま)
