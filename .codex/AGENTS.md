# Codex向け運用ワークフロー入り口

このプロジェクトのAIエージェント運用ワークフロー(Rigor Mode・フェーズ・Role・Handoff・命名・権限・レビューループ・Audit Gate)の正本は、リポジトリ直下の`agent-workflow/`にあります。作業を始める前に、必要に応じて次のファイルを読んでください。

- `agent-workflow/rules/workflows.md`: 作業単位とMode検出、フェーズとコマンドの対応、レビューループプロトコル、Audit Gate
- `agent-workflow/rules/roles.md`: Role(Manager/Architect/Programmer/Reviewer/Tester)の責務定義
- `agent-workflow/rules/naming-policy.md`: commit・branch・作業ファイルの命名規則
- `agent-workflow/rules/command-permissions.md`: 操作の権限レベルと承認ルール
- `agent-workflow/rules/policy.md`: 作業開始・変更・Gitと外部操作・完了報告の基本方針
- `agent-workflow/commands/`: フェーズ別の実行契約(読む文書・権限・副作用・次フェーズ)
- `agent-workflow/agents/`: Role別の役割・評価軸の本文
- `agent-workflow/skills/`: レビュー・docs同期・handoff確認の詳細手順

ファイルサイズを抑えるため、本文をここへ複製せず参照のみとしています。上記ファイルが見つからない場合は、そのまま作業を進めず、リポジトリ構成が想定と異なる旨を報告してください。
