# agent-workflow/agents

## 1. 概要

Architect・Reviewer・TesterというRoleの役割・評価軸の本文を置くディレクトリです。Programmerはメインエージェントが兼務し、Managerは人間PMが担うため、対応するファイルはありません。

## 2. 責任

- `architect.md`: 要件・設計・依存方向の決定、設計提案の評価軸
- `reviewer.md`: レビューループプロトコルに従った品質確認の評価軸
- `tester.md`: テスト計画・検証実行・handoff確認の評価軸

## 3. 責任外

- Claude Code固有のsubagent定義(`tools:`/`model:`フィールド、`.claude/agents/`が持ちます)
- Codex固有のagent profile定義(`.codex/agents/`が持ちます)
