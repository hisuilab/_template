# agent-workflow/commands/ship

## 1. 概要

出荷判定・記録と出荷という`ship`フェーズの実行契約を置くディレクトリです。

## 2. 責任

- `readiness.md`: 出荷判定(ready/not_ready/needs_human)の実行契約
- `pr.md`: 記録と出荷(commit・push・PR作成、Rigor Modeに応じたfast-forward mergeまたはPR経由統合)の実行契約

## 3. 責任外

- Rigor Modeの判定基準そのもの(`../../rules/workflows.md`が持ちます)
